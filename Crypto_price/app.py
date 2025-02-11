import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import json
import time
import os
import seaborn as sns
import plotly.graph_objects as go  # Added for Candlestick Chart

# Set page configuration
st.set_page_config(layout="wide", page_title="🚀 Crypto Price Tracker")

# User credentials
USER_CREDENTIALS = {
    "user": "password123",
    "admin": "password123"
}

# Login function
def login():
    st.sidebar.header("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"): 
        if USER_CREDENTIALS.get(username) == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"✅ Welcome, {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")

# Logout function
def logout():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

# Check login status
if not st.session_state.get("logged_in"):
    login()
else:
    logout()

    # App content
    image = Image.open('logo.jpg')
    st.image(image, width=500)

    st.title('💹 Crypto Price App')
    st.markdown("""
    This app retrieves cryptocurrency prices for the top 100 cryptocurrencies from **CoinMarketCap**! 🚀
    """)

    # Set API key securely
    CMC_API_KEY = os.getenv("CMC_API_KEY", "b06869a8-337b-48d7-8309-e4313b09ed18")

    # Sidebar + Main panel
    col1 = st.sidebar
    col2, col3 = st.columns((2, 1))

    # Sidebar Input Options
    col1.header('⚙️ Input Options')
    currency_price_unit = col1.selectbox('💱 Select currency for price', ('USD', 'BTC', 'ETH'))
    graph_option = col1.selectbox('📊 Select Graph Type', ['Bar Plot', 'Line Chart', 'Pie Chart', 'Heatmap', 'Scatter Plot', 'Candlestick Chart'])

    # Web scraping of CoinMarketCap data
    @st.cache_data
    def load_data():
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            try:
                coin_data = response.json()
                listings = coin_data.get('data', [])
                if not listings:
                    st.error("⚠️ No data found in API response.")
                    return pd.DataFrame()

                # Extracting data
                df = pd.DataFrame(listings)
                df = df[['name', 'symbol', 'quote']]
                df['price'] = df['quote'].apply(lambda x: x[currency_price_unit]['price'] if currency_price_unit in x else None)
                df['percentChange1h'] = df['quote'].apply(lambda x: x[currency_price_unit]['percent_change_1h'] if currency_price_unit in x else None)
                df['percentChange24h'] = df['quote'].apply(lambda x: x[currency_price_unit]['percent_change_24h'] if currency_price_unit in x else None)
                df['percentChange7d'] = df['quote'].apply(lambda x: x[currency_price_unit]['percent_change_7d'] if currency_price_unit in x else None)
                return df
            except json.JSONDecodeError:
                st.error("❗ Error decoding JSON from API response.")
                return pd.DataFrame()
        else:
            st.error(f"❌ Failed to fetch data from CoinMarketCap. Status Code: {response.status_code}")
            return pd.DataFrame()

    # Load data
    df = load_data()

    if not df.empty:
        sorted_coin = sorted(df['symbol'])
        selected_coin = col1.multiselect('💎 Select Cryptocurrencies', sorted_coin, sorted_coin[:5])
        df_selected_coin = df[df['symbol'].isin(selected_coin)]

        num_coin = col1.slider('🔢 Display Top N Coins', 1, 100, 10)
        df_coins = df_selected_coin[:num_coin]

        percent_timeframe = col1.selectbox('⏱️ Percent change timeframe', ['7d', '24h', '1h'])
        percent_dict = {"7d": 'percentChange7d', "24h": 'percentChange24h', "1h": 'percentChange1h'}
        selected_percent_timeframe = percent_dict[percent_timeframe]

        sort_values = col1.selectbox('🔽 Sort values?', ['Yes', 'No'])

        # KPIs
        col2.subheader('📈 Key Performance Indicators')
        total_market_cap = df_coins['price'].sum()
        average_price = df_coins['price'].mean()
        best_performer = df_coins.loc[df_coins[selected_percent_timeframe].idxmax()]['symbol'] if not df_coins[selected_percent_timeframe].isnull().all() else 'N/A'
        worst_performer = df_coins.loc[df_coins[selected_percent_timeframe].idxmin()]['symbol'] if not df_coins[selected_percent_timeframe].isnull().all() else 'N/A'

        col2.metric(label="🌍 Total Market Cap", value=f"{total_market_cap:,.2f} {currency_price_unit}")
        col2.metric(label="💰 Average Price", value=f"{average_price:,.2f} {currency_price_unit}")
        col2.metric(label="🚀 Best Performer", value=best_performer)
        col2.metric(label="📉 Worst Performer", value=worst_performer)

        # Display Data
        col2.subheader('🗃️ Price Data of Selected Cryptocurrencies')
        col2.dataframe(df_coins)

        # Graph Rendering
        col3.subheader(f'📊 {graph_option}')

        if graph_option == 'Bar Plot':
            plt.figure(figsize=(10, 6))
            if sort_values == 'Yes':
                df_coins = df_coins.sort_values(by=[selected_percent_timeframe])
            df_coins.plot(kind='barh', x='symbol', y=selected_percent_timeframe, color='green', ax=plt.gca())
            col3.pyplot(plt)

        elif graph_option == 'Line Chart':
            plt.figure(figsize=(10, 6))
            plt.plot(df_coins['symbol'], df_coins['price'], marker='o', linestyle='-', color='blue')
            plt.xlabel('Cryptocurrency')
            plt.ylabel(f'Price in {currency_price_unit}')
            plt.title('Cryptocurrency Price Trends')
            plt.xticks(rotation=45)
            col3.pyplot(plt)

        elif graph_option == 'Pie Chart':
            plt.figure(figsize=(8, 8))
            top_coins = df_coins.head(10)
            plt.pie(top_coins['price'], labels=top_coins['symbol'], autopct='%1.1f%%', startangle=140)
            plt.title('Top 10 Cryptocurrencies by Price')
            col3.pyplot(plt)

        elif graph_option == 'Heatmap':
            plt.figure(figsize=(8, 6))
            changes_df = df_coins[['percentChange1h', 'percentChange24h', 'percentChange7d']].corr()
            sns.heatmap(changes_df, annot=True, cmap='coolwarm', center=0)
            plt.title('Correlation of Price Changes')
            col3.pyplot(plt)

        elif graph_option == 'Scatter Plot':
            plt.figure(figsize=(10, 6))
            plt.scatter(df_coins['price'], df_coins[selected_percent_timeframe], color='purple')
            plt.xlabel(f'Price in {currency_price_unit}')
            plt.ylabel(f'% Change in {percent_timeframe}')
            plt.title(f'Price vs. {percent_timeframe} % Change')
            plt.grid(True)
            col3.pyplot(plt)

        elif graph_option == 'Candlestick Chart':
            fig = go.Figure(data=[go.Candlestick(
                x=df_coins['symbol'],
                open=df_coins['price'] * 0.95,  # Simulated open price
                high=df_coins['price'] * 1.05,  # Simulated high price
                low=df_coins['price'] * 0.90,   # Simulated low price
                close=df_coins['price']         # Actual close price
            )])
            fig.update_layout(title='📈 Candlestick Chart', xaxis_title='Cryptocurrency', yaxis_title=f'Price in {currency_price_unit}')
            col3.plotly_chart(fig)
    else:
        st.warning("⚠️ No data available. Check API key or connectivity.")
