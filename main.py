import streamlit as st
import datetime
from datetime import date
import yfinance as yf
import pandas as pd
import plotly.express as px
from statsmodels.tsa.arima.model import ARIMA
import yaml

# Load user credentials from a YAML file
def load_credentials():
    with open('credentials.yaml', 'r') as file:
        return yaml.safe_load(file)

# Check if username and password are correct
def authenticate(username, password):
    credentials = load_credentials()
    if username in credentials and credentials[username]['password'] == password:
        return True, credentials[username]['name']
    else:
        return False, None

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.user_name = ""

# Authentication
def show_login_page():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        authenticated, user_name = authenticate(username, password)
        if authenticated:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_name = user_name
            st.success(f"Welcome, {user_name}!")
            st.experimental_rerun()
        else:
            st.error("Incorrect username or password. Please try again.")

def show_app():
    app_name = "Stock Market Analysis App"
    st.title(app_name)
    st.subheader('This app forecasts the stock market price of the selected company.')
    st.image("https://img.freepik.com/free-vector/gradient-stock-market-concept_23-2149166910.jpg?size=626&ext=jpg&ga=GA1.1.2082370165.1716336000&semt=ais_user")

    st.sidebar.header('Select the parameters below')
    start_date = st.sidebar.date_input('Start date', date(2024, 1, 1))
    end_date = st.sidebar.date_input('End date', date(2024, 12, 31))
    ticker_list = ["AAPL", "MSFT", "GOOG", "GOOGL", "META", "TSLA"]
    ticker = st.sidebar.selectbox('Select the company', ticker_list)

    # Fetch data
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            st.error("No data fetched. Please check the date range or ticker symbol.")
        else:
            data.insert(0, "Date", data.index, True)
            data.reset_index(drop=True, inplace=True)
            st.write(f'Data from {start_date} to {end_date}')
            st.write(data)

            # Plot the data
            st.header("Data Visualization")
            st.subheader("Plot the data")
            st.write("**Note:** Select your specific date range from sidebar, or zoom in on the plot and select your specific column")
            fig = px.line(data, x='Date', y=data.columns, title='Closing price of the stock', width=900, height=600)
            st.plotly_chart(fig)

            # Select column for forecasting
            column = st.selectbox("Select the column to use for forecasting", data.columns[1:])
            subset_data = data[['Date', column]]
            st.write("Selected data")
            st.write(subset_data)

            # Forecasting with ARIMA
            st.header("Forecasting")
            st.subheader(f"ARIMA Forecast for {ticker}")

            def forecast_arima(data, column, periods=30):
                model = ARIMA(data[column], order=(5, 1, 0))
                model_fit = model.fit()
                forecast = model_fit.forecast(steps=periods)
                return forecast

            forecast_periods = st.slider("Select forecast periods (days)", 1, 90, 30)
            forecast = forecast_arima(subset_data, column, forecast_periods)
            forecast_dates = pd.date_range(start=subset_data['Date'].iloc[-1], periods=forecast_periods + 1)[1:]
            forecast_df = pd.DataFrame({'Date': forecast_dates, 'Forecast': forecast})

            # Merge actual and forecast data for plotting
            forecast_plot_data = pd.concat([subset_data, forecast_df], ignore_index=True)
            fig_forecast = px.line(forecast_plot_data, x='Date', y=[column, 'Forecast'], title='Stock Price Forecast', width=900, height=600)
            st.plotly_chart(fig_forecast)

            # Buy/Sell recommendation
            st.header("Buy/Sell Recommendation")
            if forecast.iloc[-1] > data[column].iloc[-1]:
                st.write("**Recommendation:** Buy")
            else:
                st.write("**Recommendation:** Sell")

    except Exception as e:
        st.error(f"Error fetching data: {e}")

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.user_name = ""
        st.experimental_rerun()

if st.session_state.authenticated:
    show_app()
else:
    show_login_page()
