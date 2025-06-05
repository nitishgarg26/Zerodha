import streamlit as st
import openai
import time
import os
from kiteconnect import KiteConnect

# --- Secrets ---
KITE_API_KEY = st.secrets["KITE_API_KEY"]
KITE_API_SECRET = st.secrets["KITE_API_SECRET"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = "your-assistant-id"  # Replace with your OpenAI Assistant ID

# --- Set OpenAI Key ---
openai.api_key = OPENAI_API_KEY

# --- Streamlit UI ---
st.title("📈 Zerodha Portfolio Chat with GPT-4o")

st.header("Step 1: Login to Zerodha")
kite = KiteConnect(api_key=KITE_API_KEY)
login_url = kite.login_url()
st.markdown(f"[Click here to login to Zerodha]({login_url})")

request_token = st.text_input("Paste the 'request_token' after login")

if request_token:
    try:
        data = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        kite.set_access_token(data["access_token"])
        st.success("✅ Logged in successfully!")

        # Step 2: Fetch Holdings
        holdings = kite.holdings()
        st.subheader("Your Holdings")
        st.dataframe(holdings)

        # Step 3: Save Holdings to File
        holding_text = "\n".join(
            [f"{h['tradingsymbol']} - Qty: {h['quantity']} @ {h['average_price']}" for h in holdings]
        )
        with open("holdings.txt", "w") as f:
            f.write(holding_text)

        # Upload to OpenAI
        uploaded_file = openai.files.create(file=open("holdings.txt", "rb"), purpose="assistants")

        # Step 4: User Query
        user_query = st.text_input("Ask something about your portfolio")
        if user_query:
            thread = openai.beta.threads.create()
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_query,
                file_ids=[uploaded_file.id]
            )

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID
            )

            with st.spinner("🤖 GPT-4o is thinking..."):
                while True:
                    status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    if status.status == "completed":
                        break
                    time.sleep(1)

            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            reply = messages.data[0].content[0].text.value
            st.markdown("### 🧠 Assistant Response")
            st.write(reply)

    except Exception as e:
        st.error(f"Error: {e}")
