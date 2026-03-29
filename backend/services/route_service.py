from __future__ import annotations

from pathlib import Path

from backend.core.config import (
    get_route_guidance_defaults_payload,
    get_scats_edges_path,
    get_scats_nodes_path,
)
from backend.core.config import normalize_data_key
from backend.route_guidance.build_scats_graph import export_scats_graph
from src.models.prediction_inference import PredictionInference
from backend.route_guidance.graph_builder import RouteGraph, load_graph_from_json
from backend.route_guidance.route_formatter import to_frontend_route
from backend.route_guidance.top_k import find_top_k_routes
from backend.route_guidance.travel_time import classify_congestion_level
from backend.route_guidance.travel_time import estimate_edge_travel_time_minutes

SUPPORTED_ALGORITHMS = {"lightgbm", "lstm", "gru"}
SUPPORTED_DATA_KEYS = {"2006", "2014"}


# Coordinate graph loading, prediction lookup, and route formatting.
class RouteService:
    # High-level backend entry point for route guidance requests.
    # Store the loaded graphs and the shared prediction helper.
    def __init__(self, graphs_by_data: dict[str, RouteGraph], model_inference: PredictionInference | None = None):
        self.graphs_by_data = graphs_by_data
        self.model_inference = model_inference

    @classmethod
    # Build a service instance from explicit graph JSON files.
    def from_json(cls, nodes_path: str | Path, edges_path: str | Path) -> "RouteService":
        return cls({"2014": load_graph_from_json(nodes_path, edges_path)})

    @classmethod
    # Load the generated SCATS/Boroondara graph for real model-aligned routing.
    # Build the default service with one graph per supported dataset.
    def from_scats_graph(cls) -> "RouteService":
        graphs_by_data = {
            data_key: cls._load_or_generate_graph(data_key)
            for data_key in SUPPORTED_DATA_KEYS
        }
        return cls(
            graphs_by_data,
            model_inference=PredictionInference(),
        )

    @staticmethod
    # Load a year-specific graph, generating it first when the files are missing.
    def _load_or_generate_graph(data_key: str) -> RouteGraph:
        normalized_data_key = normalize_data_key(data_key)
        nodes_path = get_scats_nodes_path(normalized_data_key)
        edges_path = get_scats_edges_path(normalized_data_key)
        if not nodes_path.exists() or not edges_path.exists():
            export_scats_graph(normalized_data_key)
        return load_graph_from_json(nodes_path, edges_path)

    # Return the in-memory graph for the selected dataset year.
    def get_graph(self, data_key: str = "2014") -> RouteGraph:
        normalized_data_key = data_key.strip().lower()
        if normalized_data_key not in self.graphs_by_data:
            raise ValueError(f"Unsupported data key '{data_key}'")
        return self.graphs_by_data[normalized_data_key]

    # Convert the in-memory graph back into the JSON shape expected by the frontend.
    def get_graph_payload(self, data_key: str = "2014") -> dict[str, object]:
        graph = self.get_graph(data_key)
        edges = []
        for from_node in sorted(graph.adjacency):
            for edge in graph.adjacency[from_node]:
                edges.append(
                    {
                        "from": edge.from_node,
                        "to": edge.to_node,
                        "weight": round(edge.base_time_minutes, 2),
                        "distance_km": round(edge.distance_km, 3),
                        **edge.metadata,
                    }
                )
        return {
            "data": data_key.strip().lower(),
            "nodes": [
                {
                    "id": node.id,
                    "lat": node.lat,
                    "lng": node.lng,
                    "x": 0,
                    "y": 0,
                    "label": node.label,
                }
                for node in sorted(graph.nodes.values(), key=lambda item: int(item.id))
            ],
            "edges": edges,
        }

    # Return the valid date and time options for the selected dataset year.
    def get_time_options(self, data_key: str = "2014") -> dict[str, object]:
        if self.model_inference is None:
            return {
                "data": data_key.strip().lower(),
                "available_dates": [],
                "min_date": None,
                "max_date": None,
                "times": [],
                "default_date": None,
                "default_time": None,
            }
        normalized_data_key = data_key.strip().lower()
        return self.model_inference.get_time_options(normalized_data_key)

    # Combine static defaults with dataset-specific selection options for the UI.
    def get_route_guidance_config(self) -> dict[str, object]:
        payload = get_route_guidance_defaults_payload()
        payload["selection_options"] = {
            data_key: self.get_time_options(data_key)
            for data_key in sorted(SUPPORTED_DATA_KEYS)
        }
        return payload

    # Generate top-k routes for one origin, destination, model, and timestamp.
    def get_routes(
        self,
        origin: str,
        destination: str,
        k: int = 5,
        algorithm: str = "lightgbm",
        data_key: str = "2014",
        target_datetime: str | None = None,
    ):
        normalized_algorithm = algorithm.strip().lower()
        normalized_data_key = data_key.strip().lower()

        if normalized_algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm '{algorithm}'")
        if normalized_data_key not in SUPPORTED_DATA_KEYS:
            raise ValueError(f"Unsupported data key '{data_key}'")

        graph = self.get_graph(normalized_data_key)
        if origin not in graph.nodes:
            raise ValueError(f"Origin '{origin}' does not exist in the {normalized_data_key} graph")
        if destination not in graph.nodes:
            raise ValueError(f"Destination '{destination}' does not exist in the {normalized_data_key} graph")
        if k < 1:
            raise ValueError("k must be at least 1")

        prediction_timestamp = None
        predicted_site_flows: dict[str, float] = {}
        reference_site_flows: dict[str, float] = {}
        prediction_column = f"predicted_{normalized_algorithm}"

        if self.model_inference is not None:
            prediction_timestamp, predicted_site_flows = self.model_inference.predict_site_flow_map(
                target_datetime=target_datetime,
                prediction_column=prediction_column,
                data_key=normalized_data_key,
            )
            reference_site_flows = self.model_inference.get_site_reference_flows(normalized_data_key)

        # Estimate edge cost from the predicted flow around both ends of the segment.
        def edge_cost(edge):
            from_flow = predicted_site_flows.get(edge.from_node)
            to_flow = predicted_site_flows.get(edge.to_node)
            predicted_flow = None
            if from_flow is not None and to_flow is not None:
                predicted_flow = (from_flow + to_flow) / 2.0
            elif from_flow is not None:
                predicted_flow = from_flow
            elif to_flow is not None:
                predicted_flow = to_flow

            from_reference = reference_site_flows.get(edge.from_node)
            to_reference = reference_site_flows.get(edge.to_node)
            reference_flow = None
            if from_reference is not None and to_reference is not None:
                reference_flow = (from_reference + to_reference) / 2.0
            elif from_reference is not None:
                reference_flow = from_reference
            elif to_reference is not None:
                reference_flow = to_reference

            return estimate_edge_travel_time_minutes(
                distance_km=edge.distance_km if edge.distance_km > 0 else max(edge.base_time_minutes / 60.0, 0.01),
                predicted_flow=predicted_flow,
                reference_flow=reference_flow,
                include_intersection_delay=True,
            )

        routes = find_top_k_routes(
            graph=graph,
            origin=origin,
            destination=destination,
            k=k,
            edge_cost_lookup=edge_cost,
        )
        # Attach a frontend-friendly traffic label to every segment after routing is complete.
        for route in routes:
            for segment in route.segments:
                from_flow = predicted_site_flows.get(segment.from_node)
                to_flow = predicted_site_flows.get(segment.to_node)
                from_reference = reference_site_flows.get(segment.from_node)
                to_reference = reference_site_flows.get(segment.to_node)

                predicted_flow = None
                if from_flow is not None and to_flow is not None:
                    predicted_flow = (from_flow + to_flow) / 2.0
                elif from_flow is not None:
                    predicted_flow = from_flow
                elif to_flow is not None:
                    predicted_flow = to_flow

                reference_flow = None
                if from_reference is not None and to_reference is not None:
                    reference_flow = (from_reference + to_reference) / 2.0
                elif from_reference is not None:
                    reference_flow = from_reference
                elif to_reference is not None:
                    reference_flow = to_reference

                segment.traffic_level = classify_congestion_level(predicted_flow, reference_flow)

        return {
            "algorithm": normalized_algorithm,
            "data": normalized_data_key,
            "forecast_timestamp": prediction_timestamp,
            "routes": [to_frontend_route(route, rank=index + 1) for index, route in enumerate(routes)],
        }
