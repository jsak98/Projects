import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://localhost:5101/bookings"

st.set_page_config(page_title="Car Rental Analytics", layout="wide")
st.title("🚗 Car Rental Analytics Dashboard")

# -----------------------------
# Fetch bookings
# -----------------------------
r = requests.get(API_URL)
if r.status_code == 200 and r.json():
    df = pd.DataFrame(r.json())

    # Convert to datetime (handle ISO8601 with Z)
    df["pickupDate"] = pd.to_datetime(df["pickupDate"], utc=True, infer_datetime_format=True)
    df["returnDate"] = pd.to_datetime(df["returnDate"], utc=True, infer_datetime_format=True)

    # Compute derived metrics
    df["rentalDays"] = (df["returnDate"] - df["pickupDate"]).dt.days
    df["revenue"] = df["rentalDays"] * df["dailyRate"]

    # -----------------------------
    # Key Metrics
    # -----------------------------
    total_revenue = df["revenue"].sum()
    avg_days = df["rentalDays"].mean()
    most_popular = df["carModel"].mode()[0] if not df["carModel"].empty else "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
    c2.metric("📆 Avg. Booking Length", f"{avg_days:.2f} days")
    c3.metric("🚘 Most Popular Car", most_popular)

    st.divider()

    # -----------------------------
    # Dashboard Table
    # -----------------------------
    st.subheader("📋 All Bookings")
    st.dataframe(df.sort_values("pickupDate", ascending=True), use_container_width=True)

    st.divider()

    # -----------------------------
    # Car Model Analytics
    # -----------------------------
    st.subheader("Car Model vs. Number of Rentals")
    car_counts = df["carModel"].value_counts()
    if not car_counts.empty:
        fig, ax = plt.subplots()
        car_counts.plot(kind="bar", ax=ax)
        ax.set_ylabel("Number of Rentals")
        ax.set_xlabel("Car Model")
        st.pyplot(fig)
    else:
        st.info("No data to chart.")

    st.divider()

    # -----------------------------
    # Downloads
    # -----------------------------
    st.subheader("Download Data")
    st.download_button("⬇️ Download Bookings CSV", df.to_csv(index=False), "bookings.csv", "text/csv")
    st.download_button("⬇️ Download Bookings JSON", df.to_json(orient="records"), "bookings.json", "application/json")

else:
    st.info("No bookings available for analytics.")
