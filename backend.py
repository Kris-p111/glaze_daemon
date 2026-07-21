from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
import zipfile
import io
import json
import chromadb
import torch
from transformers import AutoProcessor, CLIPModel
from transformers.image_utils import load_image
from PIL import Image
from fastapi.responses import Response
model = None
processor = None
chroma_client = None
collection = None
from tile_auto_metadata import analyze_tile_image

async def lifespan(app: FastAPI):
    global model, processor, chroma_client, collection
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True)
    processor = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")
    #chroma_client = chromadb.EphemeralClient()
    chroma_client = chromadb.HttpClient(host="chroma", port=8000)
    collection = chroma_client.get_or_create_collection(name="my_collection")
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:80",  # Frontend
    "http://127.0.0.1:80",
    "http://localhost",  # Frontend dev
    "http://127.0.0.1",
]

# Apply CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_or_create_glaze_type_id(cursor, glaze_type_name):
    """Get existing or create new glaze type and return its ID"""
    if not glaze_type_name:
        return None
    
    # Check if glaze type exists
    cursor.execute("SELECT ID FROM glazetype WHERE Name = %s", (glaze_type_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Create new glaze type
    cursor.execute("INSERT INTO glazetype (Name) VALUES (%s)", (glaze_type_name,))
    return cursor.lastrowid

def get_or_create_surface_condition_id(cursor, surface_condition_name):
    """Get existing or create new surface condition and return its ID"""
    if not surface_condition_name:
        return None
    
    # Check if surface condition exists
    cursor.execute("SELECT ID FROM surfacecondition WHERE Name = %s", (surface_condition_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Create new surface condition
    cursor.execute("INSERT INTO surfacecondition (Name) VALUES (%s)", (surface_condition_name,))
    return cursor.lastrowid

def ensure_auto_metadata_columns(cursor):
    """Keep older local databases compatible with the automated scanner."""
    cursor.execute("ALTER TABLE testpiece ADD COLUMN IF NOT EXISTS AutoTags MEDIUMTEXT DEFAULT NULL")
    cursor.execute("ALTER TABLE testpiece ADD COLUMN IF NOT EXISTS AutoKeywords MEDIUMTEXT DEFAULT NULL")
    cursor.execute("ALTER TABLE testpiece ADD COLUMN IF NOT EXISTS PrimaryColor VARCHAR(32) DEFAULT NULL")
    cursor.execute("ALTER TABLE testpiece ADD COLUMN IF NOT EXISTS DominantColors MEDIUMTEXT DEFAULT NULL")
    cursor.execute("ALTER TABLE testpiece ADD COLUMN IF NOT EXISTS ColorProfile MEDIUMTEXT DEFAULT NULL")


def json_text_or_none(value):
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)

def insert_data(data, image_data_dict):
    conn = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "tile-db"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "ceramadmin"),
        password=os.environ.get("DB_PASSWORD", "glazed-dev-password"),
        database=os.environ.get("DB_NAME", os.environ.get("MYSQL_DATABASE", "tilearchive")),
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    ensure_auto_metadata_columns(cursor)
    image_id = {}
    
    for item in data:
        ann = item.get('annotation', {})
        image_path = item.get('imageUrl', '')
        image_blob = image_data_dict.get(image_path)
        auto_metadata = analyze_tile_image(image_blob, ann)
        auto_tags = ann.get('AutoTags') or ', '.join(auto_metadata.get('tags', []))
        auto_keywords = ann.get('AutoKeywords') or auto_metadata.get('keywords', '')
        primary_color = (ann.get('PrimaryColor') or auto_metadata.get('primaryColor') or '').strip() or None
        dominant_colors = json_text_or_none(ann.get('DominantColors') or auto_metadata.get('dominantColors'))
        color_profile = json_text_or_none(ann.get('ColorProfile') or auto_metadata.get('colorProfile'))
        
        # Handle GlazeType - convert name to ID
        glaze_type_name = ann.get('GlazeType', '').strip()
        glaze_type_id = get_or_create_glaze_type_id(cursor, glaze_type_name) if glaze_type_name else None
        
        # Handle SurfaceCondition - convert name to ID  
        surface_condition_name = ann.get('SurfaceCondition', '').strip()
        surface_condition_id = get_or_create_surface_condition_id(cursor, surface_condition_name) if surface_condition_name else None
        
        # Get firing temperature, handle 0 as None
        firing_temp = ann.get('FiringTemperature')
        if firing_temp == 0:
            firing_temp = None
            
        cursor.execute("""
            INSERT INTO testpiece (
                BoardID,
                Image,
                Color_L,
                Color_A,
                Color_B,
                PrimaryColor,
                DominantColors,
                ColorProfile,
                GlazeTypeID,
                FiringTemperature,
                ChemicalComposition,
                FiringType,
                SoilType,
                SurfaceConditionID,
                AutoTags,
                AutoKeywords
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            1,  # Default BoardID
            image_blob,
            ann.get('ColorL'),
            ann.get('ColorA'),
            ann.get('ColorB'),
            primary_color,
            dominant_colors,
            color_profile,
            glaze_type_id,
            firing_temp,
            ann.get('ChemicalComposition'),
            ann.get('FiringType'),
            ann.get('SoilType'),
            surface_condition_id,
            auto_tags,
            auto_keywords
        ))
        image_id[cursor.lastrowid] = image_blob
        
    conn.commit()
    cursor.close()
    conn.close()
    return image_id

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image_data_dict = {}
        with zipfile.ZipFile(io.BytesIO(contents)) as z:
            for name in z.namelist():
                if name.endswith('annotations.json'):
                    annotations_json = z.read(name)
                    annotations = json.loads(annotations_json)
                    folder = '/'.join(name.split('/')[:-1])
                    for item in annotations:
                        img_path = item.get('imageUrl')
                        if img_path:
                            full_img_path = f"{folder}/{img_path}" if folder else img_path
                            try:
                                image_data_dict[img_path] = z.read(full_img_path)
                            except KeyError:
                                print(f"Warning: Image file {full_img_path} not found in zip")
                                image_data_dict[img_path] = None
                    image_ids = insert_data(annotations, image_data_dict)
                    for image_id, image_blob in image_ids.items():
                        image = Image.open(io.BytesIO(image_blob))
                        inputs = processor(images=image, return_tensors="pt")

                        with torch.inference_mode():
                            image_features = model.get_image_features(**inputs)
                        # tensor = image_features.pooler_output
                        embedded = image_features.pooler_output.squeeze().detach().numpy().tolist()

                        collection.add(
                            ids=[str(image_id)],
                            embeddings=[embedded],
                            metadatas=[{"tile_id": str(image_id)}]
                            )
        return {"status": "success", "message": "Data uploaded successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Upload failed: {str(e)}"}

@app.post("/search/image")
async def search_image(file: UploadFile = File(...)):
    if collection.count() == 0:
        return {"status": "error", "message": "empty tiles"}
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        inputs = processor(images=image, return_tensors="pt")

        with torch.inference_mode():
            image_features = model.get_image_features(**inputs)
        embedded = image_features.pooler_output.squeeze().detach().numpy().tolist()

        results = collection.query(
            query_embeddings=[embedded],
            n_results=2
        )
        return {
            "status": "success", 
            "matches": [
                {
                    "tile_id": tile_id, 
                    "score": score
                }
                for tile_id, score in zip(
                    results["ids"][0],
                    results["distances"][0]
                )
            ]
        }
    except Exception as e:
        return {"status": "error", "message": f"Search failed: {str(e)}"}

# @app.get("/tile/{tile_id}/image")
# async def get_tile_image(tile_id: int):
#     conn = mysql.connector.connect(
#         host=os.getenv("DB_HOST", "tile-db"),
#         user=os.getenv("DB_USER", "ceramadmin"),
#         password=os.getenv("DB_PASSWORD", ""),
#         database=os.getenv("MYSQL_DATABASE", "tilearchive"),
#         charset='utf8mb4'
#     )
#     cursor = conn.cursor()
#     cursor.execute("SELECT Image FROM testpiece WHERE ID = %s", (tile_id,))
#     result = cursor.fetchone()
#     cursor.close()
#     conn.close()
#     if result and result[0]:
#         return Response(content=result[0], media_type="image/jpeg")
#     return {"status": "error", "message": "Tile not found"}