import streamlit as st
from dotenv import load_dotenv
from api_handlers import OllamaHandler, PerplexityHandler, GroqHandler
from utils import generate_response, litellm_config, litellm_instructions
from config_menu import config_menu, display_config
from logger import logger
import os
from handlers.litellm_handler import LiteLLMHandler

# Load environment variables from .env file
load_dotenv()

def load_css():
    # Load custom CSS styles
    with open(os.path.join(os.path.dirname(__file__), "..", "static", "styles.css")) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def setup_page():
    # Configure the Streamlit page
    st.set_page_config(page_title="multi1-research: LLM reasoning frontend", page_icon="🧠", layout="wide")
    load_css()
    
    # Display the main title
    st.markdown("""
    <h1 class="main-title">
        🧠 multi1-research: LLM reasoning frontend
    </h1>
    """, unsafe_allow_html=True)
    
    # Display the app description
    st.markdown("""
    <p class="main-description">
        Inference using reasoning chains using different backends. Compared to the original project, this fork adds various prompting configuration options.
    </p>
    """, unsafe_allow_html=True)

def get_api_handler(backend, config):
    if backend == "Ollama":
        return OllamaHandler(config['OLLAMA_URL'], config['OLLAMA_MODEL'])
    elif backend == "Perplexity AI":
        return PerplexityHandler(config['PERPLEXITY_API_KEY'], config['PERPLEXITY_MODEL'])
    elif backend == "Groq":
        return GroqHandler(config['GROQ_API_KEY'], config['GROQ_MODEL'])
    else:  # LiteLLM
        litellm_config = st.session_state.get('litellm_config', {})
        return LiteLLMHandler(
            litellm_config.get('model', ''),
            litellm_config.get('api_base', ''),
            litellm_config.get('api_key', '')
        )

def main():
    logger.info("Starting the application")
    
    setup_page()

    # Initialize config panel
    st.sidebar.markdown("## Configuration")
    
    # Allow user to select the AI backend   
    backend = st.sidebar.selectbox("Choose AI Backend", ["LiteLLM", "Ollama", "Perplexity AI", "Groq"], index=1)
    logger.info(f"Selected backend: {backend}")
    
    config = config_menu()
    
    print(f"\n[main()] Current Ollama model: {config['OLLAMA_MODEL']}")
    
    if backend == "LiteLLM":
        litellm_instructions()
        litellm_config()
    else:
        display_config(backend, config)
    
    api_handler = get_api_handler(backend, config)
    
    # User input field
    user_query_disabled = False if config['PROMPT_SOURCE']=="Text field" else True
    user_query_placeholder = "e.g. \"How many 'R's are in the word strawberry?\""
    user_query_field = st.text_area("Enter your query:", placeholder=(user_query_placeholder if not user_query_disabled else "Text input is disabled when a different input source has been set."), height=150, disabled=user_query_disabled)
    
    # conditional on query source

    # if st.button("Generate response") & len(user_query_field) > 0:
    if st.button("Generate response"):
        logger.info(f"User query text field disabled: {user_query_disabled}; user query text field contents: {user_query_field}")
        st.write("Generating response...")
        response_container = st.empty()
        #time_container = st.empty()

        try:
            # Generate and display the response
            for steps, total_thinking_time in generate_response(user_query_field, api_handler):
                with response_container.container():
                    for title, content, _ in steps:
                        if title.lower().startswith("final answer"):
                            print(f"\n[main: main() generation loop] {title}: {content}")
                            # Display the final answer
                            st.markdown(f'<h3 class="expander-title">{title}</h3>', unsafe_allow_html=True)
                            st.markdown(f'<div>{content}</div>', unsafe_allow_html=True)
                            logger.info(f"Final answer generated: {content}")
                        else:
                            # Display intermediate steps
                            with st.expander(f"📝 {title}", expanded=True):
                                st.markdown(f'<div>{content}</div>', unsafe_allow_html=True)
                            logger.debug(f"Step completed: {title}")

                # Display total thinking time
                if total_thinking_time is not None:
                    st.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**") # Eliminate wobble of original version
                    #time_container.markdown(f'<p class="thinking-time">Total thinking time: {total_thinking_time:.2f} seconds</p>', unsafe_allow_html=True)
                    logger.info(f"Total thinking time: {total_thinking_time:.2f} seconds")
        except Exception as e:
            # Handle and display any errors
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            st.error("An error occurred while generating the response. Please try again.")

if __name__ == "__main__":
    main()