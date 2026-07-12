import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from prophet import Prophet  # type: ignore
    HAS_PROPHET = True
except ImportError:
    Prophet = None
    HAS_PROPHET = False

try:
    from xgboost import XGBRegressor  # type: ignore
    HAS_XGBOOST = True
except ImportError:
    XGBRegressor = None
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMRegressor  # type: ignore
    HAS_LIGHTGBM = True
except ImportError:
    LGBMRegressor = None
    HAS_LIGHTGBM = False


def generate_forecast_chart(df: pd.DataFrame):
    """
    Generate a simple linear forecast visualization for numeric columns.
    Shows historical data + predicted trend.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    date_cols = []
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() >= 0.7:
                df[col] = parsed
                date_cols.append(col)
    if not date_cols:
        date_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns.tolist()
    forecasts = []

    for col in numeric_cols:
        try: 
            if date_cols:
                date_col = date_cols[0]
                series_df = (
                    df[[date_col, col]]
                    .dropna()
                    .sort_values(date_col)
                    .groupby(pd.Grouper(key=date_col, freq="D"))[col]
                    .sum()
                    .reset_index()
                )
                series_df = series_df[series_df[col].notna()]
                if len(series_df) < 5:
                    continue
                x_values = series_df[date_col]
                data = series_df[col].reset_index(drop=True)
            else:
                data = df[col].dropna().reset_index(drop=True)
                x_values = pd.RangeIndex(start=0, stop=len(data), step=1)
            if len(data) < 3:
                continue

            X = np.arange(len(data)).reshape(-1, 1)
            y = data.values.astype(float)

            if HAS_SKLEARN:
                model = LinearRegression()
                model.fit(X, y)
                predict = model.predict
            else:
                slope, intercept = np.polyfit(np.arange(len(data)), y, 1)
                predict = lambda values: intercept + slope * values.reshape(-1)

            forecast_steps = 30 if date_cols else max(7, min(30, len(data) // 4))
            X_forecast = np.arange(len(data) + forecast_steps).reshape(-1, 1)
            y_forecast = predict(X_forecast)
            residual_std = float(np.std(y - predict(X), ddof=1)) if len(data) > 2 else 0

            if date_cols:
                last_date = pd.to_datetime(x_values.iloc[-1])
                forecast_x = pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_steps, freq="D")
                observed_x = x_values
            else:
                observed_x = list(range(len(data)))
                forecast_x = list(range(len(data), len(data) + forecast_steps))

            observed_y = y
            forecast_y = y_forecast[len(data):]
            upper = forecast_y + (1.96 * residual_std)
            lower = forecast_y - (1.96 * residual_std)

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=observed_x,
                y=observed_y,
                mode='lines+markers',
                name='Past data',
                line=dict(color='#22c55e', width=2),
                marker=dict(size=5),
            ))

            fig.add_trace(go.Scatter(
                x=forecast_x,
                y=forecast_y,
                mode='lines',
                name='Next 30 days forecast' if date_cols else 'Future forecast',
                line=dict(color='#f59e0b', width=3, dash='dash'),
            ))

            fig.add_trace(go.Scatter(
                x=list(forecast_x) + list(forecast_x)[::-1],
                y=list(upper) + list(lower)[::-1],
                fill='toself',
                fillcolor='rgba(245, 158, 11, 0.18)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo='skip',
                name='Confidence range',
            ))

            fig.update_layout(
                title=f"{col.replace('_', ' ').title()} future forecast",
                xaxis_title="Date" if date_cols else "Future period",
                yaxis_title=col.replace("_", " ").title(),
                hovermode='x unified',
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=32, r=32, t=44, b=32),
            )

            forecasts.append({
                "chart": fig.to_json(),
                "type": "forecast",
                "column": col,
                "model": "Linear Regression" if HAS_SKLEARN else "Linear trend fallback",
                "confidence_score": 70 if residual_std else 60,
                "reasoning": f"Projected {col} from the observed historical trend.",
                "contributing_features": [date_cols[0], col] if date_cols else ["row_sequence", col],
                "business_explanation": f"The forecast extends the recent direction of {col} into the next planning periods.",
                "recommended_action": "Use this as an early directional signal and validate it with known business events before acting.",
            })

        except Exception as e:
            print(f"Forecast generation failed for {col}: {str(e)}")
            continue

    return forecasts


def _time_series_frame(df: pd.DataFrame, date_col: str, target_col: str) -> pd.DataFrame:
    frame = df[[date_col, target_col]].copy()
    frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
    frame[target_col] = pd.to_numeric(frame[target_col], errors="coerce")
    frame = frame.dropna().sort_values(date_col)
    if frame.empty:
        return frame
    return frame.groupby(pd.Grouper(key=date_col, freq="D"))[target_col].sum().reset_index().dropna()


def generate_ml_forecasts(df: pd.DataFrame, dataset_profile: dict, periods: int = 30):
    """Generate explainable forecast records with optional Prophet/XGBoost/LightGBM engines."""
    numeric_cols = dataset_profile.get("numeric_columns", [])[:6]
    date_cols = dataset_profile.get("datetime_columns", [])
    forecasts = []
    if not numeric_cols:
        return forecasts

    for target in numeric_cols:
        try:
            if date_cols:
                date_col = date_cols[0]
                series = _time_series_frame(df, date_col, target)
                if len(series) < 8:
                    continue
                y = series[target].astype(float).values
                x = np.arange(len(series)).reshape(-1, 1)
            else:
                series = pd.DataFrame({target: pd.to_numeric(df[target], errors="coerce").dropna().reset_index(drop=True)})
                if len(series) < 8:
                    continue
                y = series[target].astype(float).values
                x = np.arange(len(series)).reshape(-1, 1)

            candidates = []
            if HAS_PROPHET and date_cols:
                try:
                    prophet_df = series.rename(columns={date_cols[0]: "ds", target: "y"})[["ds", "y"]]
                    model = Prophet(interval_width=0.9)
                    model.fit(prophet_df)
                    future = model.make_future_dataframe(periods=periods)
                    prediction = model.predict(future).tail(periods)
                    forecast_values = prediction["yhat"].tolist()
                    candidates.append(("Prophet", forecast_values, 0.82, ["time_index", target]))
                except Exception:
                    pass
            if HAS_XGBOOST:
                try:
                    model = XGBRegressor(n_estimators=80, random_state=42, objective="reg:squarederror")
                    model.fit(x, y)
                    future_x = np.arange(len(series), len(series) + periods).reshape(-1, 1)
                    candidates.append(("XGBoost Regressor", model.predict(future_x).tolist(), 0.78, ["time_index", target]))
                except Exception:
                    pass
            if HAS_LIGHTGBM:
                try:
                    model = LGBMRegressor(n_estimators=80, random_state=42, verbose=-1)
                    model.fit(x, y)
                    future_x = np.arange(len(series), len(series) + periods).reshape(-1, 1)
                    candidates.append(("LightGBM", model.predict(future_x).tolist(), 0.78, ["time_index", target]))
                except Exception:
                    pass
            if HAS_SKLEARN:
                model = RandomForestRegressor(n_estimators=80, random_state=42)
                model.fit(x, y)
                future_x = np.arange(len(series), len(series) + periods).reshape(-1, 1)
                score = max(0.0, min(1.0, float(model.score(x, y))))
                candidates.append(("Random Forest fallback", model.predict(future_x).tolist(), score, ["time_index", target]))

            if not candidates:
                slope, intercept = np.polyfit(np.arange(len(y)), y, 1)
                future_x = np.arange(len(series), len(series) + periods)
                candidates.append(("Linear trend fallback", (intercept + slope * future_x).tolist(), 0.58, ["time_index", target]))

            model_name, values, confidence, features = sorted(candidates, key=lambda item: item[2], reverse=True)[0]
            current = float(y[-1])
            predicted = float(values[-1])
            change_percent = None if current == 0 else round((predicted - current) / abs(current) * 100, 2)
            forecasts.append({
                "type": "forecast",
                "column": target,
                "model": model_name,
                "horizon_periods": periods,
                "current_value": round(current, 2),
                "predicted_value": round(predicted, 2),
                "forecast_values": [round(float(value), 2) for value in values],
                "change_percent": change_percent,
                "confidence_score": int(round(confidence * 100)),
                "reasoning": f"{model_name} projected {target} using historical sequence patterns from the uploaded data.",
                "contributing_features": features,
                "business_explanation": f"If recent patterns continue, {target} may reach {round(predicted, 2)} over the forecast horizon.",
                "recommended_action": "Compare this forecast with business plans, seasonality, and known upcoming events before committing targets.",
            })
        except Exception:
            continue
    return forecasts
