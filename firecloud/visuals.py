import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import CLOUD_LAYERS_KM
from .geometry import earth_shadow_min_altitude_km


def cross_section_figure(snapshot: pd.DataFrame, direction_offset: float, solar_altitude_deg: float,
                         selected_voxels: pd.DataFrame | None = None):
    g = snapshot[snapshot["direction_offset_deg"] == direction_offset].sort_values("distance_km")
    d = np.linspace(0, 440, 221)
    shadow = [earth_shadow_min_altitude_km(x, solar_altitude_deg) for x in d]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d, y=shadow, mode="lines", name="地球蒙影頂部"))

    # Cloud cover as vertical rectangles at each forecast sample.
    for _, row in g.iterrows():
        x = float(row["distance_km"])
        for layer, (z0, z1) in CLOUD_LAYERS_KM.items():
            key = {"low":"cloud_cover_low", "mid":"cloud_cover_mid", "high":"cloud_cover_high"}[layer]
            cc = row.get(key)
            if pd.isna(cc) or float(cc) <= 1:
                continue
            fig.add_shape(type="rect", x0=x-7, x1=x+7, y0=z0, y1=z1,
                          opacity=min(0.75, 0.08 + float(cc)/140.0), line_width=0)

    if selected_voxels is not None and not selected_voxels.empty:
        v = selected_voxels[selected_voxels["direction_offset_deg"] == direction_offset]
        for _, r in v.iterrows():
            eff = r.get("effective_illuminated_cloud")
            if pd.isna(eff) or eff <= 0.02:
                continue
            fig.add_trace(go.Scatter(
                x=[r["distance_km"]],
                y=[(r["layer_bottom_km"]+r["layer_top_km"])/2],
                mode="markers",
                marker={"size": 8 + 22*float(eff)},
                name="受光 Canvas",
                showlegend=False,
                hovertemplate=f"{r['layer']}<br>有效受光={float(eff):.2f}<extra></extra>"
            ))

    for x, label in [(40,"40"),(100,"100"),(300,"300"),(350,"350"),(440,"440")]:
        fig.add_vline(x=x, line_dash="dot")
    fig.update_layout(
        title=f"太陽方向垂直剖面｜方向 {direction_offset:+.0f}°｜太陽高度角 {solar_altitude_deg:.1f}°",
        xaxis_title="朝太陽方向地表距離 (km)",
        yaxis_title="離地高度 AGL (km)",
        yaxis_range=[0, 18],
        height=560,
    )
    return fig


def route_map_figure(route_df: pd.DataFrame, observer_lat: float, observer_lon: float):
    import plotly.express as px
    df = route_df.copy()
    fig = px.scatter_map(df, lat="lat", lon="lon", color="direction_offset_deg",
                         hover_data=["distance_km", "direction_offset_deg"],
                         labels={"direction_offset_deg":"方向偏移 (°)", "distance_km":"距離 (km)", "lat":"緯度", "lon":"經度"},
                         zoom=5, height=500)
    fig.add_scattermap(lat=[observer_lat], lon=[observer_lon], mode="markers+text",
                       text=["觀測點"], textposition="top center", marker={"size": 14}, name="觀測點")
    fig.update_layout(map_style="open-street-map", margin={"l":0,"r":0,"t":30,"b":0})
    return fig


def illumination_matrix_figure(matrix_df: pd.DataFrame, solar_altitude_deg: float):
    """Heatmap of geometric illumination state by distance and cloud altitude."""
    m = matrix_df[matrix_df["solar_altitude_deg"] == float(solar_altitude_deg)].copy()
    if m.empty:
        return go.Figure()
    piv = m.pivot(index="cloud_altitude_km", columns="distance_km", values="illuminated").astype(int)
    piv = piv.sort_index(ascending=True)
    fig = go.Figure(go.Heatmap(
        x=list(piv.columns),
        y=list(piv.index),
        z=piv.values,
        zmin=0,
        zmax=1,
        colorbar={"title": "0=蒙影 / 1=受光", "tickvals": [0,1], "ticktext": ["蒙影", "受光"]},
        hovertemplate="距離=%{x} km<br>雲高=%{y} km<br>狀態=%{z}<extra></extra>",
    ))
    for x in (40, 100, 300, 350, 440):
        fig.add_vline(x=x, line_dash="dot")
    fig.update_layout(
        title=f"Canvas 受光矩陣｜太陽高度角 {solar_altitude_deg:.1f}°",
        xaxis_title="朝太陽方向地表距離 (km)",
        yaxis_title="雲高 AGL (km)",
        height=520,
    )
    return fig


def dynamic_rez_figure(rez_df: pd.DataFrame):
    """Dynamic geometric REZ entry distance across the civil-twilight timeline."""
    fig = go.Figure()
    for z in sorted(rez_df["cloud_altitude_km"].unique()):
        g = rez_df[rez_df["cloud_altitude_km"] == z].sort_values("solar_altitude_deg", ascending=False)
        fig.add_trace(go.Scatter(
            x=g["solar_altitude_deg"],
            y=g["dynamic_rez_entry_distance_km"],
            mode="lines+markers",
            name=f"{z:g} km 雲高",
        ))
    fig.add_hline(y=350, line_dash="dot")
    fig.add_hline(y=440, line_dash="dot", annotation_text="Legacy REZ 440 km（非 Dynamic 上限）")
    fig.update_layout(
        title="不同雲高的動態 REZ 幾何起始距離",
        xaxis_title="太陽高度角 (°)",
        yaxis_title="朝太陽方向首次獲得直射光的距離 (km)",
        yaxis_range=[0, 460],
        height=520,
    )
    return fig


def forecast_voxel_illumination_figure(
    voxel_df: pd.DataFrame,
    solar_altitude_deg: float,
    direction_offset_deg: float = 0.0,
    metric: str = "effective_illuminated_cloud_proxy",
):
    """Heatmap combining forecast cloud occupancy with geometric illumination."""
    m = voxel_df[
        (voxel_df["solar_altitude_deg"] == float(solar_altitude_deg))
        & (voxel_df["direction_offset_deg"] == float(direction_offset_deg))
    ].copy()
    if m.empty:
        return go.Figure()

    labels = {
        "effective_illuminated_cloud_proxy": "有效受光雲量代理",
        "cloud_cover_fraction": "預報雲量比例",
        "upstream_transmission_proxy": "上游穿透率代理",
        "illuminated_fraction_of_present_cloud_proxy": "現有雲體受光比例代理",
    }
    if metric not in labels:
        metric = "effective_illuminated_cloud_proxy"

    piv = m.pivot(index="cloud_altitude_km", columns="distance_km", values=metric).sort_index()
    hover = []
    for z in piv.index:
        line = []
        for d in piv.columns:
            q = m[(m["cloud_altitude_km"] == z) & (m["distance_km"] == d)].iloc[0]
            cc = q["cloud_cover_fraction"]
            tr = q["upstream_transmission_proxy"]
            ef = q["effective_illuminated_cloud_proxy"]
            line.append(
                f"距離={d:g} km<br>雲高={z:g} km<br>層={q['forecast_layer']}"
                f"<br>狀態={q['voxel_state']}"
                f"<br>雲量={'Missing' if pd.isna(cc) else f'{cc:.2f}'}"
                f"<br>上游穿透率={'Missing' if pd.isna(tr) else f'{tr:.2f}'}"
                f"<br>有效受光={'Missing' if pd.isna(ef) else f'{ef:.2f}'}"
            )
        hover.append(line)

    fig = go.Figure(go.Heatmap(
        x=list(piv.columns),
        y=list(piv.index),
        z=piv.values,
        zmin=0, zmax=1,
        customdata=hover,
        colorbar={"title": labels[metric]},
        hovertemplate="%{customdata}<extra></extra>",
    ))
    for x in (40, 100, 300, 350, 440):
        fig.add_vline(x=x, line_dash="dot")
    fig.update_layout(
        title=(f"預報雲體 × 受光｜方向 {direction_offset_deg:+.0f}°｜"
               f"太陽高度角 {solar_altitude_deg:.1f}°"),
        xaxis_title="朝太陽方向地表距離 (km)",
        yaxis_title="診斷雲高 AGL (km)",
        height=540,
    )
    return fig


def reconstructed_voxel_figure(df, solar_altitude_deg, direction_offset_deg, metric="effective_illuminated_cloud_volume_proxy"):
    import plotly.graph_objects as go
    g = df[(df["solar_altitude_deg"] == solar_altitude_deg) &
           (df["direction_offset_deg"] == direction_offset_deg)].copy()
    if g.empty:
        return go.Figure()
    p = g.pivot(index="voxel_center_km", columns="distance_km", values=metric).sort_index(ascending=True)
    metric_labels = {
        "effective_illuminated_cloud_volume_proxy": "有效受光雲體積代理",
        "cloud_occupancy_proxy": "雲體占據率代理",
        "cloud_occupancy": "雲體占據率",
        "geometric_illuminated_fraction": "幾何受光比例",
        "upstream_transmission_proxy": "上游穿透率代理",
        "remaining_transmission_proxy": "剩餘穿透率代理",
        "slant_cloud_optical_depth_proxy": "斜向雲光學厚度代理",
        "relative_humidity_pct": "相對濕度 (%)",
        "native_metric_value": "原生雲微物理量",
    }
    fig = go.Figure(data=go.Heatmap(x=p.columns, y=p.index, z=p.values, colorbar=dict(title=metric_labels.get(metric, metric))))
    if metric in {"remaining_transmission_proxy", "remaining_native_cloud_transmission_estimate"} and "upstream_path_state" in g.columns:
        endpoint = g.loc[g["upstream_path_state"] == "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK", "distance_km"]
        if not endpoint.empty:
            endpoint_x = float(endpoint.max())
            fig.add_vline(x=endpoint_x, line_dash="dot", line_color="#f59e0b", opacity=0.9)
            fig.add_annotation(x=endpoint_x, y=1.02, yref="paper", text="路徑終點：未檢查上游", showarrow=False,
                               font=dict(size=11, color="#f59e0b"), xanchor="right")
    fig.update_layout(title=f"0.5 km 重建雲體 Voxel｜太陽高度角 {solar_altitude_deg}°｜方向 {direction_offset_deg:+.0f}°",
                      xaxis_title="朝太陽方向地表距離 (km)", yaxis_title="離地高度 AGL (km)")
    return fig
