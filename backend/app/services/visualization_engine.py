import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def style_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=32, r=32, t=44, b=32),
        font=dict(size=12),
    )
    return fig


def generate_visualizations(df: pd.DataFrame):
    charts = []

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()

    # ===============================
    # 🔥 Histogram (numeric)
    # ===============================
    for col in numeric_cols:
        fig = px.histogram(
            df,
            x=col,
            title=f"{col} distribution",
            nbins=28,
            opacity=0.85,
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        style_chart(fig)
        charts.append({
            "chart": fig.to_json(),
            "type": "histogram",
            "column": col,
        })

    # ===============================
    # 🔥 Box plot (numeric)
    # ===============================
    for col in numeric_cols:
        fig = px.box(
            df,
            y=col,
            title=f"{col} spread and outliers",
            points="outliers",
            color_discrete_sequence=px.colors.sequential.Viridis,
        )
        style_chart(fig)
        charts.append({
            "chart": fig.to_json(),
            "type": "box",
            "column": col,
        })

    # ===============================
    # 🔥 Scatter plot (numeric pairs)
    # ===============================
    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[:2]
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            title=f"{y_col} vs {x_col}",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig.update_traces(marker=dict(size=9, opacity=0.85, line=dict(width=1, color="DarkSlateGrey")))
        style_chart(fig)
        charts.append({
            "chart": fig.to_json(),
            "type": "scatter",
            "column": f"{x_col},{y_col}",
        })

    # ===============================
    # 🔥 Bar chart + pie chart (categorical)
    # ===============================
    for col in categorical_cols:
        value_counts = df[col].value_counts().head(10).reset_index()
        value_counts.columns = [col, "count"]

        bar = px.bar(
            value_counts,
            x=col,
            y="count",
            title=f"Top values for {col}",
            color="count",
            color_continuous_scale=px.colors.sequential.Agsunset,
        )
        style_chart(bar)
        charts.append({
            "chart": bar.to_json(),
            "type": "bar",
            "column": col,
        })

        if len(value_counts) > 1:
            pie = px.pie(
                value_counts,
                names=col,
                values="count",
                title=f"Category share for {col}",
                hole=0.38,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            style_chart(pie)
            charts.append({
                "chart": pie.to_json(),
                "type": "pie",
                "column": col,
            })

    # ===============================
    # 🔥 Line chart (date + numeric)
    # ===============================
    for col in df.columns:
        if "date" in col.lower() or col in datetime_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df_sorted = df.sort_values(by=col).dropna(subset=[col])

                for num_col in numeric_cols:
                    fig = px.line(
                        df_sorted,
                        x=col,
                        y=num_col,
                        title=f"{num_col} over time",
                        markers=True,
                        color_discrete_sequence=px.colors.qualitative.Bold,
                    )
                    style_chart(fig)
                    charts.append({
                        "chart": fig.to_json(),
                        "type": "line",
                        "column": num_col,
                    })
            except Exception:
                pass

    if not datetime_cols and numeric_cols:
        index_df = df.reset_index().rename(columns={'index': 'row'})
        for num_col in numeric_cols:
            fig = px.line(
                index_df,
                x="row",
                y=num_col,
                title=f"{num_col} trend by row",
                markers=True,
                color_discrete_sequence=px.colors.qualitative.Dark24,
            )
            style_chart(fig)
            charts.append({
                "chart": fig.to_json(),
                "type": "line",
                "column": num_col,
            })

    # ===============================
    # 🔥 Correlation heatmap (numeric)
    # ===============================
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        heatmap = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            colorscale='Blues',
            zmin=-1,
            zmax=1,
            colorbar=dict(title="correlation"),
        ))
        heatmap.update_layout(title='Numeric correlation heatmap')
        style_chart(heatmap)
        charts.append({
            "chart": heatmap.to_json(),
            "type": "heatmap",
            "column": ",".join(numeric_cols[:2]),
        })

    return charts
