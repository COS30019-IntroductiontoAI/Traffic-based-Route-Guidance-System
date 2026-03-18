import { Map, MapControls } from "@/components/ui/map";
import { Card } from "@/components/ui/card";

export default function RouteGuidance() {
  return (
    <Card className="h-[calc(100vh-120px)] w-full p-0 overflow-hidden rounded-2xl">
      <Map center={[-74.006, 40.7128]} zoom={11}>
        <MapControls 
          position="top-left"
          showZoom
          showCompass
          showLocate
          showFullscreen
        />
      </Map>
    </Card>
  );
}