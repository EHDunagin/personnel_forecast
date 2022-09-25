import pandas as pd
from tkinter import filedialog

def date_range(start, periods):
    """
    Input -> 
    start - date from which to start projection. Precision at a monthly level will be used.
    periods - integer indicating number of months to project
    Output -> DataFrame of month start and end dates

    Creates and returns DataFrame of month start and end dates from start date and number of months.
    """
   
    date_df = pd.DataFrame(
        data={
            "month_starts": pd.date_range(
                start=start.replace(day=1),
                periods=periods,
                freq="MS",
            ),
            "month_ends": pd.date_range(
                start=start,
                periods=periods,
                freq="M",
            ),
        }
    )

    return date_df

def forecast(date_df, fringe, positions, inflation):
    """
    Input -> DataFrames with input information to use to generate forecast
        
        positions: information about positions to forecast includes columns
            position_id
            position_title
            department
            employee_id
            employee_name
            salary_annual
            bonus_rate
            commission_rate
            start_date
            end_date
        inflation: expected inflation rates includes columns "inflation_date" and "inflation_rate" (from start)
    Output -> DataFrame of forecast of expense by employee for each month from start to end (based on number of months)
    of forecast range with rows for salary bonus commission and fringe.
    """
    
    # Fill in missing employee start and end dates with min or min timestamps
    positions["start_date"] = positions["start_date"].fillna(value=pd.Timestamp.min)
    positions["end_date"] = positions["end_date"].fillna(value=pd.Timestamp.max)

    # Calculate monthly salary, bonus, commission, and fringe amounts. Shifts these values from columns to rows.
    forecast_df = positions.assign(
        salary=positions["salary_annual"] / 12,
        bonus=positions["salary_annual"] * positions["bonus_rate"] / 12,
        commission=positions["salary_annual"] * positions["commission_rate"] / 12,
        fringe=positions["salary_annual"] * fringe / 12,
    ).melt(
        id_vars=[
            "position_id",
            "position_title",
            "department",
            "employee_id",
            "employee_name",
            "start_date",
            "end_date",
        ],
        value_vars=["salary", "bonus", "commission", "fringe"],
        var_name="expense_type",
        value_name="expense_amount",
    )

    # Filter to exclude amounts of 0
    forecast_df = forecast_df[forecast_df["expense_amount"] != 0]

    # Cross join personnel info to date DF.
    forecast_df = date_df.merge(forecast_df, how="cross")

    # Filter to exclude months before start or after end of specific employee
    forecast_df = forecast_df[
        (forecast_df["start_date"] <= forecast_df["month_ends"])
        & (forecast_df["end_date"] >= forecast_df["month_starts"])
    ]

    # Calculates proration of month from start and end.
    forecast_df["proration"] = (
        (
            forecast_df[["end_date", "month_ends"]].min(axis=1)
            - forecast_df[["start_date", "month_starts"]].max(axis=1)
        ).dt.days
        + 1
    ) / ((forecast_df["month_ends"] - forecast_df["month_starts"]).dt.days + 1)

    # Joins inflation data.
    forecast_df = pd.merge_asof(
        forecast_df, inflation, left_on="month_starts", right_on="inflation_date"
    )
    forecast_df["inflation_rate"] = forecast_df["inflation_rate"].fillna(value=1)

    # Calculates forecast amount from monthly amount, proration, and applicable inflation.
    forecast_df["expense_amount"] = (
        forecast_df["expense_amount"]
        * forecast_df["proration"]
        * forecast_df["inflation_rate"]
    )

    # Add headcount column with 1 in headcount on "salary" line iff start date is before and end date is after end of month.
    forecast_df["headcount"] = (
        (forecast_df["start_date"] <= forecast_df["month_ends"])
        & (forecast_df["end_date"] >= forecast_df["month_ends"])
        & (forecast_df["expense_type"] == "salary")
    ).astype("int")

    return forecast_df


def get_inputs(fpath):
    """
    Input -> Filepath to Excel file with input info
    Output -> DataFrames with input information to use to generate forecast
    """
    settings = pd.read_excel(fpath, sheet_name="settings", index_col=0)
    positions = pd.read_excel(fpath, sheet_name="positions")
    inflation = pd.read_excel(fpath, sheet_name="inflation")
    return settings, positions, inflation


if __name__ == "__main__":
    # Prompt for filepath
    fpath = filedialog.askopenfilename(
        title="Select inputs file", filetypes=[("Microsoft Excel Worksheet", "*.xlsx")]
    )

    output_path = (
        filedialog.askdirectory(title="Select output directory ")
        + "/output_personnel_forecast.csv"
    )

    settings, positions, inflation = get_inputs(fpath)

    date_df = date_range(settings.loc["start_date", "setting"], settings.loc["months", "setting"])

    print("Here is the date_df\n", date_df)

    forecast(date_df, settings.loc["fringe", "setting"], positions, inflation).to_csv(output_path)
