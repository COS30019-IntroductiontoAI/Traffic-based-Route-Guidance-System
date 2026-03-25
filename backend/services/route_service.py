from __future__ import annotations

from pathlib import Path

from backend.core.config import (
    SCATS_EDGES_PATH,
    SCATS_NODES_PATH,
)
from backend.models.prediction_inference import PredictionInference
from backend.route_guidance.graph_builder import RouteGraph, load_graph_from_json
from backend.route_guidance.route_formatter import to_frontend_route
from backend.route_guidance.top_k import find_top_k_routes
from backend.route_guidance.travel_time import estimate_edge_travel_time_minutes

SUPPORTED_ALGORITHMS = {"lightgbm", "lstm", "gru"}
SUPPORTED_DATA_KEYS = {"2006", "2014"}


class RouteService:
    # High-level backend entry point for route guidance requests.
    def __init__(self, graph: RouteGraph, model_inference: PredictionInference | None = None):
        self.graph = graph
        self.model_inference = model_inference

    @classmethod
    def from_json(cls, nodes_path: str | Path, edges_path: str | Path) -> "RouteService":
        return cls(load_graph_from_json(nodes_path, edges_path))

    @classmethod
    # Load the generated SCATS/Boroondara graph for real model-aligned routing.
    def from_scats_graph(cls) -> "RouteService":
        return cls(
            load_graph_from_json(SCATS_NODES_PATH, SCATS_EDGES_PATH),
            model_inference=PredictionInference(),
        )

    def get_routes(
        self,
        origin: str,
        destination: str,
        k: int = 5,
        algorithm: str = "lightgbm",
        data_key: str = "2014",
    ):
        normalized_algorithm = algorithm.strip().lower()
        normalized_data_key = data_key.strip().lower()

        if normalized_algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm '{algorithm}'")
        if normalized_data_key not in SUPPORTED_DATA_KEYS:
            raise ValueError(f"Unsupported data key '{data_key}'")

        prediction_timestamp = None
        predicted_site_flows: dict[str, float] = {}
        reference_site_flows: dict[str, float] = {}
        prediction_column = f"predicted_{normalized_algorithm}"

        if self.model_inference is not None:
            prediction_timestamp, predicted_site_flows = self.model_inference.predict_site_flow_map(
                prediction_column=prediction_column,
                data_key=normalized_data_key,
            )
            reference_site_flows = self.model_inference.get_site_reference_flows(normalized_data_key)

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
                include_intersection_delay=False,
            )

        routes = find_top_k_routes(
            graph=self.graph,
            origin=origin,
            destination=destination,
            k=k,
            edge_cost_lookup=edge_cost,
        )
        return {
            "algorithm": normalized_algorithm,
            "data": normalized_data_key,
            "forecast_timestamp": prediction_timestamp,
            "routes": [to_frontend_route(route, rank=index + 1) for index, route in enumerate(routes)],
        }
