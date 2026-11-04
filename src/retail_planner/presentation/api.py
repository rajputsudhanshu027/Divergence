"""Read-only batch forecast API and an adjustable retrospective order scenario."""

from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..evaluation.inventory import order_scenario


class ScenarioRequest(BaseModel):
    series_id: str
    cushion_percentile: Literal[0.8, 0.9, 0.95] = 0.9
    shortage_cost: float = Field(default=5.0, ge=0, le=10000)
    excess_cost: float = Field(default=1.0, ge=0, le=10000)


def create_app(report_dir: Path) -> FastAPI:
    result_path = report_dir / "results.json"
    if not result_path.is_file():
        raise FileNotFoundError(f"No report at {result_path}; run a study first")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in result["series"]}
    app = FastAPI(title="Retail Demand Planner", version="0.1.0",
                  description="Precomputed M5 forecasts and a transparent inventory scenario")

    @app.get("/health")
    def health():
        return {"status": "ok", "source": result["source"],
                "series_count": result["series_count"]}

    @app.get("/metrics")
    def metrics():
        return {key: result[key] for key in ("profile", "validation", "holdout", "monitoring", "inventory")}

    @app.get("/series")
    def list_series(store: str | None = None, category: str | None = None,
                    limit: int = Query(default=100, ge=1, le=1000)):
        rows = (row for row in result["series"]
                if (store is None or row["store"] == store)
                and (category is None or row["category"] == category))
        return [{"id": row["id"], "item": row["item"], "store": row["store"],
                 "category": row["category"]} for _, row in zip(range(limit), rows)]

    @app.get("/forecast/{series_id}")
    def forecast_series(series_id: str):
        row = by_id.get(series_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Series not found")
        return {"selected_method": result["selected_method"],
                "forecast_dates": result["forecast_dates"], **row}

    @app.post("/scenario")
    def scenario(request: ScenarioRequest):
        row = by_id.get(request.series_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Series not found")
        actual = sum(row["holdout_actual"])
        level = str(request.cushion_percentile)
        selected = order_scenario(
            sum(row["holdout_predicted"]), actual, row["holdout_on_hand"],
            row["holdout_scale"], result["inventory"]["cushions"]["selected"][level],
            request.shortage_cost, request.excess_cost,
        )
        baseline = order_scenario(
            sum(row["holdout_baseline"]), actual, row["holdout_on_hand"],
            row["holdout_scale"], result["inventory"]["cushions"]["seasonal_28"][level],
            request.shortage_cost, request.excess_cost,
        )
        selected_future_target = sum(row["forecast"]) + \
            result["inventory"]["cushions"]["selected"][level] * row["future_scale"]
        baseline_future_target = sum(row["future_baseline"]) + \
            result["inventory"]["cushions"]["seasonal_28"][level] * row["future_scale"]
        return {"series_id": request.series_id, "holdout_start": result["holdout_start"],
                "cushion_percentile": request.cushion_percentile, "actual_units": actual,
                "selected": selected, "seasonal_28": baseline,
                "future_order_units": max(0, ceil(
                    max(0.0, selected_future_target) - row["future_on_hand"])),
                "future_baseline_order_units": max(0, ceil(
                    max(0.0, baseline_future_target) - row["future_on_hand"])),
                "future_on_hand_assumed": row["future_on_hand"]}

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(report_dir / "index.html")

    return app
