import os
from io import BytesIO

import requests
from bson import Binary, ObjectId
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from backend.db import get_database, upload_embeddings_to_mongo
from backend.schema import FileContent, PostInfo
from backend.utils.embedding import find_top_matches, generate_text_embedding
from backend.utils.regex_ptr import extract_info
from backend.utils.steganography import (decode_text_from_image,
                                         encode_text_in_image)
from backend.utils.text_llm import (create_poem, decompose_user_text,
                                    expand_user_text_using_gemini,
                                    expand_user_text_using_gemma,
                                    text_to_image)
from backend.utils.twitter import send_message_to_twitter

app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility function to convert ObjectId to string
def serialize_object_id(document):
    """Recursively convert ObjectId to string in MongoDB documents."""
    if isinstance(document, dict):
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
            elif isinstance(value, dict):
                document[key] = serialize_object_id(value)
    return document


# Routes
@app.post("/text-generation")
async def get_post_and_expand_its_content(post_info: PostInfo):
    """Expand user input text for help message generation."""
    try:
        concatenated_text = (
            f"Name: {post_info.name}\n"
            f"Phone: {post_info.phone}\n"
            f"Location: {post_info.location}\n"
            f"Duration of Abuse: {post_info.duration_of_abuse}\n"
            f"Frequency of Incidents: {post_info.frequency_of_incidents}\n"
            f"Preferred Contact Method: {post_info.preferred_contact_method}\n"
            f"Current Situation: {post_info.current_situation}\n"
            f"Culprit Description: {post_info.culprit_description}\n"
            f"Custom Text: {post_info.custom_text}\n"
        )
        gemini_response = await expand_user_text_using_gemini(concatenated_text)
        gemma_response = await expand_user_text_using_gemma(concatenated_text)
        return {"gemini_response": gemini_response, "gemma_response": gemma_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error expanding text: {e}")


@app.post("/img-generation")
async def create_image_from_prompt(input_data: str):
    """Generate an image based on a text prompt."""
    try:
        text_to_image(input_data)
        return {"received_text": input_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")


@app.post("/text-decomposition")
async def get_text_and_decompose_its_content(text: str):
    """Decompose and extract information from user text."""
    try:
        decomposed_text = decompose_user_text(text)
        extracted_data = extract_info(decomposed_text)
        return {"extracted_data": extracted_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decomposing text: {e}")


@app.post("/encode")
async def encode_text(text: str, img_url: str = None, file: UploadFile = File(None)):
    """Encode text into an image."""
    try:
        if bool(img_url) == bool(file):
            raise HTTPException(
                status_code=400, detail="Provide either an image URL or file, not both."
            )

        image = (
            Image.open(BytesIO(requests.get(img_url).content))
            if img_url
            else Image.open(file.file)
        )
        encoded_image = encode_text_in_image(image, text)

        output_path = "encoded_image.png"
        encoded_image.save(output_path, format="PNG")

        return StreamingResponse(
            open(output_path, "rb"),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=encoded_image.png"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error encoding text in image: {e}"
        )


@app.post("/decode")
async def decode_text(img_url: str = None, file: UploadFile = File(None)):
    """Decode text from an image."""
    try:
        if bool(img_url) == bool(file):
            raise HTTPException(
                status_code=400, detail="Provide either an image URL or file, not both."
            )

        image = (
            Image.open(BytesIO(requests.get(img_url).content))
            if img_url
            else Image.open(file.file)
        )
        decoded_text = decode_text_from_image(image)
        return {"decoded_text": decoded_text}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decoding text from image: {e}"
        )


@app.get("/poem-generation")
async def create_inspiring_poems(text: str):
    """Generate an inspirational poem based on input text."""
    try:
        return {"poem": create_poem(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating poem: {e}")


@app.post("/send-message")
async def send_message(image_url: str, caption: str):
    """Send a message to Twitter."""
    try:
        send_message_to_twitter(image_url, caption)
        return {"status": "Message sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error sending message to Twitter: {e}"
        )


@app.get("/get-all-posts")
def get_all_posts():
    """Retrieve all posts from the database."""
    try:
        # Database connection
        db = get_database()
        posts = [serialize_object_id(post) for post in db["posts"].find()]
        return JSONResponse(content=posts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving posts: {e}")


@app.get("/find-match")
def get_top_matches(info: str):
    """Find top matches based on embedding similarity."""
    try:
        # Database connection
        db = get_database()
        description_vector = generate_text_embedding(info)
        top_matches = find_top_matches(db["complains2"], description_vector)
        return [serialize_object_id(match) for match in top_matches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding matches: {e}")


@app.get("/get-post/{post_id}")
def get_post_by_id(post_id: str):
    """Retrieve a specific post by its ID."""
    try:
        # Database connection
        db = get_database()
        post = db["posts"].find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return JSONResponse(content=serialize_object_id(post))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving post by ID: {e}")



# Directory containing docs
docs_dir = "backend/docs"


# Function to read files from the docs directory with improved error handling for encoding
def read_files_from_directory(directory: str):
    file_contents = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                file_contents.append((filename, content))
            except UnicodeDecodeError:
                print(f"Error reading {filename} as UTF-8. Trying a different encoding...")
                try:
                    with open(file_path, "r", encoding="latin-1") as file:
                        content = file.read()
                    file_contents.append((filename, content))
                except Exception as e:
                    print(f"Failed to read {filename} with both UTF-8 and latin-1 encodings. Error: {e}")
    return file_contents


import pickle


# FastAPI endpoint to trigger reading and uploading files
@app.post("/upload_embeddings/")
async def upload_embeddings():
    try:
        # Read files from the docs directory
        file_contents = read_files_from_directory(docs_dir)

        # Upload embeddings to MongoDB
        upload_embeddings_to_mongo(file_contents)

        return {"message": "Embeddings uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint to encode and store a single document (for testing)
@app.post("/upload_single_document/")
async def upload_single_document(file_content: FileContent):
    try:
        # Generate embeddings for the document content
        embedding = encode_text(file_content.content)

        # Prepare the document to insert into MongoDB
        doc = {
            "filename": file_content.filename,
            "embedding": Binary(pickle.dumps(embedding)),
            "content": file_content.content[:500]
        }
        db = get_database()
        collection = db["doc_embedding"]
        # Insert the document into the MongoDB collection
        collection.insert_one(doc)

        return {"message": f"Uploaded {file_content.filename} to MongoDB successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))