from transformers import pipeline

# This line initializes the summarization pipeline.
# The first time this code is run, it will download the BART-CNN model (over 1GB).
# After the first run, it will use the cached version, so startup will be fast.
print("Loading BART-CNN summarization model...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
print("Model loaded successfully.")

def summarize_text_with_bart(text_content: str) -> str:
    """
    Uses a local BART-CNN model to summarize the given text.
    """
    try:
        # Transformer models have a token limit. We'll truncate the text to
        # a reasonable length to prevent errors with very long documents.
        # A more advanced approach would be to chunk the text and summarize each chunk.
        max_chunk_length = 1024  # BART's default max length
        
        # We perform the summarization on the first chunk of the text.
        summary_list = summarizer(
            text_content[:max_chunk_length * 5], # Send a reasonably sized chunk
            max_length=150, 
            min_length=40, 
            do_sample=False
        )
        
        # The result is a list containing a dictionary. We extract the summary text.
        return summary_list[0]['summary_text']
        
    except Exception as e:
        print(f"An error occurred while summarizing with BART: {e}")
        return "Error: Could not generate summary."