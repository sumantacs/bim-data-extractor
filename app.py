import streamlit as st
import google.generativeai as genai
import os
import tempfile

# --- App Configuration ---
st.set_page_config(page_title="BIM Data Extractor", page_icon="🏗️", layout="wide")
st.title("🏗️ Civil Engineering BIM Extractor")
st.write("Upload a modern PDF design or a scanned old paper blueprint to extract structural dimensions, lengths, widths, and materials.")

# --- API Key Setup ---
api_key = st.text_input("Enter your Gemini API Key:", type="password")
if api_key:
    genai.configure(api_key=api_key)

# --- File Uploader ---
uploaded_file = st.file_uploader("Upload Blueprint or Design", type=['pdf', 'jpg', 'jpeg', 'png'])

if uploaded_file and api_key:
    st.info("File uploaded successfully. Ready for extraction.")
    
    if st.button("Extract BIM Data"):
        with st.spinner("Analyzing design and extracting measurements... this may take a minute."):
            try:
                # Save the uploaded file to a temporary location so the Gemini API can read it
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                # Upload the file to Google's generative AI storage
                gemini_file = genai.upload_file(path=tmp_file_path)

                # Initialize Gemini 1.5 Pro (Best for multimodal tasks like reading PDFs/Images)
                model = genai.GenerativeModel('gemini-1.5-pro-latest')

                # Strict prompt to format the output like a BIM system
                prompt = '''
                You are an expert Civil Engineer and BIM (Building Information Modeling) specialist.
                Review the attached design document carefully. Extract the following information and present it in a highly structured format:
                
                1. Document Summary: What kind of design is this?
                2. Key Dimensions: List all detectable lengths, widths, heights, and areas. (Put this in a Markdown table).
                3. Structural Elements: Identify walls, columns, beams, doors, and windows.
                4. Materials & Annotations: Note any specific materials mentioned or handwritten notes.
                5. Confidence/Visibility Issues: Explicitly state if any parts of the document are unreadable, faded, or ambiguous.
                
                Accuracy is critical. If a measurement is unclear, state "Unclear" rather than guessing.
                '''

                # Generate the response
                response = model.generate_content([gemini_file, prompt])
                
                # Display results
                st.success("Extraction Complete!")
                st.markdown("### Extracted Data")
                st.markdown(response.text)

                # Cleanup temporary files
                os.remove(tmp_file_path)
                
            except Exception as e:
                st.error(f"An error occurred during extraction: {e}")
elif not api_key:
    st.warning("Please enter your Gemini API Key to proceed.")
