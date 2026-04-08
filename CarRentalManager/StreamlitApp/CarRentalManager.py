import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://localhost:5101/bookings"

st.set_page_config(page_title="Car Rental Manager", layout="wide")
st.title("Car Rental Manager")

menu = ["Dashboard", "Add Booking", "Edit Booking", "Delete Booking", "Analytics"]
choice = st.sidebar.radio("Navigation", menu)

# -----------------------------
# Fetch all bookings
# -----------------------------
def fetch_bookings():
    r = requests.get(API_URL)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        if not df.empty:
            # Convert string dates to datetime.date
            df["pickupDate"] = pd.to_datetime(df["pickupDate"]).dt.date
            df["returnDate"] = pd.to_datetime(df["returnDate"]).dt.date
            df["rentalDays"] = (pd.to_datetime(df["returnDate"]) - pd.to_datetime(df["pickupDate"])).dt.days
            df["revenue"] = df["rentalDays"] * df["dailyRate"]
        return df
    return pd.DataFrame()

# -----------------------------
# Dashboard
# -----------------------------
if choice == "Dashboard":
    st.subheader("All Bookings")
    df = fetch_bookings()
    if df.empty:
        st.info("No bookings found.")
    else:
        st.dataframe(df)
        # Metrics
        total_revenue = df["revenue"].sum()
        avg_days = df["rentalDays"].mean()
        most_popular = df["carModel"].mode()[0] if not df["carModel"].mode().empty else "—"

# -----------------------------
# Add Booking
# -----------------------------
elif choice == "Add Booking":
    st.subheader("Add Booking")
    bookingId = st.text_input("Booking ID")
    customerName = st.text_input("Customer Name")
    carModel = st.text_input("Car Model")
    pickupDate = st.text_input("Pickup Date (YYYY-MM-DD)")
    returnDate = st.text_input("Return Date (YYYY-MM-DD)")
    dailyRate = st.number_input("Daily Rate", min_value=1)

    if st.button("Add Booking"):
        payload = {
            "bookingId": bookingId,
            "customerName": customerName,
            "carModel": carModel,
            "pickupDate": pickupDate,
            "returnDate": returnDate,
            "dailyRate": int(dailyRate)
        }
        r = requests.post(API_URL, json=payload)
        if r.status_code == 201:
            st.success("✅ Booking added!")
        else:
            st.error(f"Failed: {r.text}")

# -----------------------------
# Edit Booking
# -----------------------------
elif choice == "Edit Booking":
    st.subheader("Edit Booking")
    booking_id = st.text_input("Booking ID to Edit")
    if st.button("Fetch"):
        r = requests.get(f"{API_URL}/{booking_id}")
        if r.status_code == 200:
            data = r.json()
            st.session_state.edit_data = data
        else:
            st.warning("Booking not found.")

    if "edit_data" in st.session_state:
        data = st.session_state.edit_data
        customerName = st.text_input("Customer Name", value=data["customerName"])
        carModel = st.text_input("Car Model", value=data["carModel"])
        pickupDate = st.text_input("Pickup Date (YYYY-MM-DD)", value=data["pickupDate"])
        returnDate = st.text_input("Return Date (YYYY-MM-DD)", value=data["returnDate"])
        dailyRate = st.number_input("Daily Rate", min_value=1, value=int(data["dailyRate"]))

        if st.button("Update Booking"):
            payload = {
                "bookingId": booking_id,
                "customerName": customerName,
                "carModel": carModel,
                "pickupDate": pickupDate,
                "returnDate": returnDate,
                "dailyRate": int(dailyRate)
            }
            r = requests.put(f"{API_URL}/{booking_id}", json=payload)
            if r.status_code == 200:
                st.success("✅ Booking updated!")
                del st.session_state.edit_data
            else:
                st.error(f"Failed: {r.text}")

# -----------------------------
# Delete Booking
# -----------------------------
elif choice == "Delete Booking":
    st.subheader("Delete Booking")
    booking_id = st.text_input("Booking ID to Delete")
    if st.button("Delete"):
        r = requests.delete(f"{API_URL}/{booking_id}")
        if r.status_code in (200, 204):
            st.success("Booking deleted!")
        else:
            st.error(f"Failed: {r.text}")

# -----------------------------
# Analytics
# -----------------------------
elif choice == "Analytics":
    st.subheader("Analytics")
    df = fetch_bookings()
    if df.empty:
        st.info("No bookings available for analytics.")
    else:
        # Ensure date columns are date-only
        df["pickupDate"] = pd.to_datetime(df["pickupDate"]).dt.date
        df["returnDate"] = pd.to_datetime(df["returnDate"]).dt.date

        # Derived metrics
        df["rentalDays"] = (pd.to_datetime(df["returnDate"]) - pd.to_datetime(df["pickupDate"])).dt.days
        df["revenue"] = df["rentalDays"] * df["dailyRate"]

        # -----------------------------
        # Key Metrics
        # -----------------------------
        total_revenue = df["revenue"].sum()
        avg_length = df["rentalDays"].mean()
        most_popular_car = df["carModel"].mode()[0] if not df["carModel"].empty else "—"
        total_bookings = len(df)
        unique_customers = df["customerName"].nunique()
        unique_cars = df["carModel"].nunique()

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total Revenue", f"Rs.{total_revenue:.2f}")
        col2.metric("Avg. Booking Length", f"{avg_length:.1f} days")
        col3.metric("Most Popular Car", most_popular_car)
        col4.metric("Total Bookings", total_bookings)
        col5.metric("Unique Customers", unique_customers)
        col6.metric("Unique Car Models", unique_cars)

        st.divider()

        # -----------------------------
        # Top 3 Most Rented Cars
        # -----------------------------
        st.subheader("Top 3 Most Rented Cars")
        top3 = df["carModel"].value_counts().head(3)
        st.bar_chart(top3)

        st.divider()

        # -----------------------------
        # Bookings Trend Over Time
        # -----------------------------
        st.subheader("Bookings Trend Over Time")
        bookings_per_day = pd.Series(0, index=pd.date_range(df["pickupDate"].min(), df["returnDate"].max()))
        for _, row in df.iterrows():
            bookings_per_day[pd.date_range(row["pickupDate"], row["returnDate"])] += 1
        st.line_chart(bookings_per_day)

        st.divider()

        # -----------------------------
        # Revenue Trend Over Time
        # -----------------------------
        st.subheader("Revenue Trend Over Time")
        revenue_per_day = pd.Series(0, index=pd.date_range(df["pickupDate"].min(), df["returnDate"].max()))
        for _, row in df.iterrows():
            days = pd.date_range(row["pickupDate"], row["returnDate"])
            daily_revenue = row["dailyRate"]
            revenue_per_day[days] += daily_revenue
        st.line_chart(revenue_per_day)

        st.divider()

        # -----------------------------
        # Top 5 Customers by Revenue
        # -----------------------------
        st.subheader("Top 5 Customers by Revenue")
        top_customers = df.groupby("customerName")["revenue"].sum().sort_values(ascending=False).head(5)
        st.bar_chart(top_customers)

        st.divider()

        # -----------------------------
        # Downloads
        # -----------------------------
        st.subheader("Download Data")
        st.download_button("Download Bookings CSV", df.to_csv(index=False), "bookings.csv", "text/csv")
        st.download_button("Download Analytics JSON", df.to_json(orient="records"), "analytics.json", "application/json")

