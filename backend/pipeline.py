import pandas as pd
from hdbscan import approximate_predict
import numpy as np

def pipeline_crime_hotspot(df: pd.DataFrame, days: int, models):
    """Runs the complete hotspot forecasting pipeline.

    This function applies spatial clustering to the input crime data,
    identifies hotspot clusters, and performs time series forecasting
    for each detected hotspot using pre-trained models.

    Args:
        df (pd.DataFrame): Input DataFrame containing crime records. Must include
            'latitude', 'longitude', and 'data_ocorrencia' columns.
        days (int): Number of future days to forecast.
        models (dict): Dictionary containing trained models for HDBSCAN clustering
            and time series forecasting. Must include a key "hdbscan" for the clusterer.

    Returns:
        list[dict]: A list of forecast results, where each entry represents
            predicted crime occurrences for a hotspot.

    Raises:
        ValueError: If the HDBSCAN clusterer is not provided in the models dictionary.

    Example:
        >>> forecasts = pipeline_crime_hotspot(df, days=7, models=models)
        >>> print(forecasts[0])
        {'ds': '2025-10-10', 'mean_crimes': 12.4, 'min_crimes': 9.2, ...}
    """
    clusterer = models.get("hdbscan", None)
    if not clusterer:
        raise ValueError("HDBSCAN clusterer model not found in 'models'.")

    df = pipeline_clusterer(df, clusterer)

    hotspot_ids = [
        str(int(hotspot_id))
        for hotspot_id in df["hotspot_id"].dropna().unique()
        if hotspot_id and hotspot_id != -1
    ]
    print(hotspot_ids)

    selected_models = [
        {hotspot: model} for hotspot, model in models.items() if hotspot in hotspot_ids
    ]
    print(selected_models)

    forecasts = []

    for selected_model in selected_models:
        hotspot_id = list(selected_model.keys())[0]
        print(f"Processing hotspot_id: {hotspot_id}")

        filtered_df = df[df["hotspot_id"] == float(hotspot_id)]
        if filtered_df.empty:
            print(f"No data available for hotspot_id: {hotspot_id}, skipping forecast.")
            continue

        forecast = pipeline_forecast(
            days=days,
            hotspot_id=float(hotspot_id),
            df=filtered_df,
            model=selected_model[hotspot_id],
        )

        forecasts.extend(forecast.to_dict(orient="records"))

    return forecasts


def pipeline_forecast(days: int, hotspot_id: float, df: pd.DataFrame, model):
    """Generates crime forecasts for a specific hotspot.

    This function aggregates crime occurrences by date, fits a time series
    forecasting model, and outputs the predicted number of crimes for the
    specified forecast horizon.

    Args:
        days (int): Number of future days to forecast.
        hotspot_id (float): Identifier of the hotspot to forecast.
        df (pd.DataFrame): DataFrame containing historical crime data for the hotspot.
            Must include 'data_ocorrencia', 'latitude', and 'longitude' columns.
        model: A trained forecasting model (e.g., StatsForecast, AutoARIMA).

    Returns:
        pd.DataFrame: Forecast results with columns:
            - 'ds': Forecasted dates.
            - 'mean_crimes': Predicted mean number of crimes.
            - 'min_crimes': Lower bound of 95% confidence interval.
            - 'max_crimes': Upper bound of 95% confidence interval.
            - 'latitude', 'longitude': Mean coordinates of the hotspot.
            - 'hotspot_id': ID of the hotspot.

    Example:
        >>> result = pipeline_forecast(7, 1.0, df_hotspot, arima_model)
        >>> result.head()
                ds  mean_crimes  min_crimes  max_crimes  latitude  longitude  hotspot_id
        0  2025-10-10        12.4         9.2        15.8 -23.5596  -46.6357         1.0
    """
    ts = df.groupby("data_ocorrencia").size().reset_index(name="y")
    ts["unique_id"] = str(0.0)
    ts = ts.rename(columns={"data_ocorrencia": "ds"})

    # Forecast future crime counts
    fcst = model.forecast(df=ts, h=days, level=[95])

    lat = df["latitude"].mean()
    lon = df["longitude"].mean()

    fcst["hotspot_id"] = hotspot_id
    fcst["latitude"] = lat
    fcst["longitude"] = lon

    fcst.rename(
        columns={
            "AutoARIMA": "mean_crimes",
            "AutoARIMA-lo-95": "min_crimes",
            "AutoARIMA-hi-95": "max_crimes",
        },
        inplace=True,
    )

    fcst = fcst.replace([np.inf, -np.inf], np.nan).fillna(0)

    return fcst

def pipeline_clusterer(df: pd.DataFrame, model):
    """Assigns hotspot cluster IDs to crime data using HDBSCAN.

    This function converts geographic coordinates into radians and predicts
    cluster assignments for each point using a pre-trained HDBSCAN model.

    Args:
        df (pd.DataFrame): Input DataFrame containing crime data. Must include
            'latitude' and 'longitude' columns.
        model: Trained HDBSCAN clusterer model.

    Returns:
        pd.DataFrame: Updated DataFrame with a new 'hotspot_id' column
            representing the cluster assignment for each crime record.

    Example:
        >>> df = pipeline_clusterer(df, clusterer)
        >>> df[['latitude', 'longitude', 'hotspot_id']].head()
           latitude  longitude  hotspot_id
        0 -23.5596   -46.6357          1
        1 -23.5621   -46.6428          1
        2 -23.5732   -46.6211          2
    """
    coords = df[["latitude", "longitude"]].dropna()
    coords_radians = np.radians(coords)

    hotspot_ids, _ = approximate_predict(clusterer=model, points_to_predict=coords_radians)  # type: ignore

    df.loc[coords.index, "hotspot_id"] = hotspot_ids

    return df