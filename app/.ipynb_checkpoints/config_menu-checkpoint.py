import streamlit as st
import os
from dotenv import load_dotenv, set_key
try:
    import ollama
except ImportError:
    pass

def load_env_vars():
    print("\nLoading config from .env file...")
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    return {
        'OLLAMA_URL': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
        'OLLAMA_MODEL': os.getenv('OLLAMA_MODEL', 'mistral'),
        'PERPLEXITY_API_KEY': os.getenv('PERPLEXITY_API_KEY', ''),
        'PERPLEXITY_MODEL': os.getenv('PERPLEXITY_MODEL', 'mistral-7b-instruct'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY', ''),
        'GROQ_MODEL': os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
        'PROMPT_SOURCE': os.getenv('PROMPT_SOURCE', 'Text field'),
        'PROMPT_FILE': os.getenv('PROMPT_FILE', 'default_prompt_source_file.txt'),
        'PROMPT_SEPARATOR': os.getenv('PROMPT_SEPARATOR', '//'),
        'SAVE_OUTPUT': os.getenv('SAVE_OUTPUT', 'No'),
        'OUTPUT_FILENAME': os.getenv('OUTPUT_FILENAME', 'default_output_file.txt'),
        'NUM_RUNS': os.getenv('NUM_RUNS', '1')
    }

def get_ollama_models(config):
    try:
        ollama_models = ollama.list()
        #return [model['name'] for model in ollama_models['models']]
        return [model.model for model in ollama_models.models]
        print("Ollama models fetched successfully.")
    except Exception as e:
        print("Error: Could not fetch Ollama models. Falling back to default.")
        return [config['OLLAMA_MODEL']]  # Return default model if fetching fails

def save_env_vars():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    new_config = {key: value for key, value in st.session_state.items()}
    print(f"\n[config_menu: save_env_vars()] Saving env variables: {new_config}")
    # establish valid fields and save keys corresponding to them from session_state
    valid_env_fields = ['OLLAMA_URL','OLLAMA_MODEL','PERPLEXITY_API_KEY','PERPLEXITY_MODEL','GROQ_API_KEY','GROQ_MODEL','PROMPT_SOURCE','PROMPT_FILE','PROMPT_SEPARATOR','SAVE_OUTPUT','OUTPUT_FILENAME','NUM_RUNS']
    for key, value in new_config.items():
        if key in valid_env_fields and not value == None:
            print(f"/nSaving key {key}, value {value}")
            set_key(env_path, key, str(value)) # ensure string (converts NUM_RUNS)
        else:
            pass

def config_menu():
    # note that this function automatically returns the updated values of the variables and does not wait for a separate "apply changes" step
    
    print("DEBUG: Entered config_menu()")

    # Load env vars on app start-up
    # Env vars should only be loaded on app start-up and not after this (unless done manually for some reason)
    print(f"DEBUG: hasattr(config_menu, 'first_init_completed') evaluates as {hasattr(config_menu, 'first_init_completed')}")
    if not hasattr(config_menu, 'first_init_completed'):
        print("\nLoading env vars to initialize config_menu()...")
        config = load_env_vars()
        config_menu.first_init_completed = True
    else:
        config = config_menu.saved_config_from_menu
    
    # Load models
    ollama_models = get_ollama_models(config)
    
    # Backend configuration panel allows the user to define the settings for different backends
    with st.sidebar.expander("Backend configuration"):
        st.text_input("Ollama URL", value=config['OLLAMA_URL'], key='OLLAMA_URL')
        print(f"\n[config_menu: config_menu()] Ollama models: {ollama_models}")

        default_model = config['OLLAMA_MODEL']
        if default_model in ollama_models:
            default_index = ollama_models.index(default_model)
        else:
            default_index = 0  # fallback to first model
        
        st.selectbox("Ollama model", ollama_models, index=default_index, key='OLLAMA_MODEL')
        
        st.text_input("Perplexity API key", value=config['PERPLEXITY_API_KEY'], type="password", key='PERPLEXITY_API_KEY')
        st.text_input("Perplexity model", value=config['PERPLEXITY_MODEL'], key='PERPLEXITY_MODEL')
        st.text_input("Groq API key", value=config['GROQ_API_KEY'], type="password", key='GROQ_API_KEY')
        st.text_input("Groq model", value=config['GROQ_MODEL'], key='GROQ_MODEL')
        
        if st.button("Save backend config"):
            print(f"\n[config_menu: config_menu()] Accessing save_env_vars() to save configuration...")
            save_env_vars()
            config = {key: value for key, value in st.session_state.items()}
            st.success("Configuration saved successfully!")

        # Option for manually reloading configuration (not used)
        # if st.button("Reload configuration"):
        #     load_env_vars()
        #     print(f"\n[config_menu: config_menu()] New configuration loaded: {config}")
        #     st.success("Configuration reloaded from .env successfully!")

    # Workflow configuration to e.g. set the prompt source and choose whether to save the output
    with st.sidebar.expander("Workflow configuration"):
        # Prompt source selection
        prompt_source_options = ["Text field", "Upload file (single prompt)", "Upload file (multiple prompts)"]
        prompt_source = st.radio(
            label="Prompt source",
            options=prompt_source_options,
            index=prompt_source_options.index(config['PROMPT_SOURCE']),
            key="PROMPT_SOURCE"
        )
    
        if "Upload file" in prompt_source:
            user_prompt_file = st.file_uploader("Upload a file containing the prompt", type=["txt"], key="PROMPT_FILE")
    
            if "multiple prompts" in prompt_source.lower():
                st.text_input("Separator symbol(s)", key="PROMPT_SEPARATOR")
    
            if user_prompt_file:
                user_prompt = user_prompt_file.read().decode()
                if "multiple prompts" in prompt_source.lower() and st.session_state.get("PROMPT_SEPARATOR"):
                    prompts = user_prompt.split(st.session_state["PROMPT_SEPARATOR"])
                    preview = [prompts[0][:50], prompts[1][:50]] if len(prompts) > 1 else [prompts[0][:50]]
                else:
                    preview = [user_prompt[:100]]
                with st.popover("Preview prompt"):
                    st.markdown("\n\n".join(preview))
    
        # Output saving
        st.radio("Save output to CSV", options=["No", "Yes"], index=0, key="SAVE_OUTPUT")
    
        if st.session_state.get("SAVE_OUTPUT") == "Yes":
            st.text_input("Output filename", key="OUTPUT_FILENAME")
    
        st.number_input("Number of runs (not yet implemented", min_value=1, max_value=1000, value=1, step=1, key="NUM_RUNS")
    
        # Save configuration button
        if st.button("Save workflow config"):
            print("\n[config_menu] Saving config via Save button in workflow section...")
            save_env_vars()
            config = {key: value for key, value in st.session_state.items()}
            st.success("Configuration saved successfully!")

    # Old variant with Streamlit Form used - consider rollback as necessary
    # with st.sidebar.expander("Workflow configuration"):
    #     # Override default text box input and instead read a specified file as input
    #     with st.form(key="workflow_config"):
    #         prompt_source_options = ["Text field", "Upload file (single prompt)", "Upload file (multiple prompts)"]
    #         prompt_source = st.radio(label="Prompt source", options=prompt_source_options, index=prompt_source_options.index(config['PROMPT_SOURCE']), key="PROMPT_SOURCE")
    #         if st.form_submit_button("Set prompt source"):
    #             #st.session_state.PROMPT_SOURCE = "file" if prompt_source == "Upload file" else "text_field"
    #             pass # simply passing will have the sidebar reload, and therefore show the elements below as appropriate
    #         if ("Upload file" in st.session_state.PROMPT_SOURCE):
    #             user_prompt_file = st.file_uploader("Upload a file containing the prompt", type=["txt"], key="PROMPT_FILE")
    #             if (prompt_source == "Upload file (multiple prompts)"):
    #                 multi_prompt_separator = st.text_input("Separator symbol(s)", key="PROMPT_SEPARATOR")
    #             if user_prompt_file:
    #                 # NB: reading the file for prompt preview purposes
    #                 user_prompt = user_prompt_file.read().decode()
    #                 if (prompt_source == "Upload file (multiple prompts)") and len(multi_prompt_separator)>0:
    #                     user_prompt = user_prompt.split(multi_prompt_separator)
    #                     prompt_preview = [user_prompt[0][:50],  {user_prompt[1][:50]}]
    #                     print(f"\n[config_menu: config_menu()] Previewing prompt from uploaded file: {prompt_preview}...")
    #                 else:
    #                     prompt_preview = {user_prompt[:100]}
    #                     print(f"\n[config_menu: config_menu()] Previewing prompt from uploaded file: {prompt_preview}...")
    #                 with st.popover(label="Preview prompt"):
    #                     st.markdown(prompt_preview)
            
    #         # Enable saving of output into a specified file
    #         output_saving = st.radio(label="Save output to CSV", options=["No", "Yes"], index=0, key="SAVE_OUTPUT")
    #         if st.form_submit_button("Set output"):
    #             pass
    #         if output_saving == "Yes":
    #             output_filename = st.text_input("Output filename", key="OUTPUT_FILENAME")
    #         number_of_runs = st.number_input("Number of runs", min_value=1, max_value=1000, value=1, step=1, key="NUM_RUNS")
    #         if st.form_submit_button("Save workflow config"):
    #             print(f"\n[config_menu: config_menu()] Accessing save_env_vars() to save configuration...")
    #             save_env_vars()
    #             config = {key: value for key, value in st.session_state.items()}
    #             st.success("Configuration saved successfully!")
        
        # Enable saving of output into a specified file
        # if st.button("Save output to file"):
        #     output_file = st.text_input("Output file name")
        #     if not output_file.endswith(".txt"):
        #         output_file += ".txt"
        #     with open(output_file, "w") as f:
        #         f.write(user_query)
        #     st.success(f"Response saved successfully to {output_file}!")

        
    config_menu.saved_config_from_menu = config # save config in function attribute to avoid variables being lost
    return config


def display_config(backend, config):
    st.sidebar.markdown("## Current configuration")
    if backend == "Ollama":
        st.sidebar.markdown(f"- Ollama URL: `{config['OLLAMA_URL']}`")
        st.sidebar.markdown(f"- Ollama Model: `{config['OLLAMA_MODEL']}`")
    elif backend == "Perplexity AI":
        st.sidebar.markdown(f"- Perplexity AI Model: `{config['PERPLEXITY_MODEL']}`")
    elif backend == "Groq":
        st.sidebar.markdown(f"- Groq Model: `{config['GROQ_MODEL']}`")
