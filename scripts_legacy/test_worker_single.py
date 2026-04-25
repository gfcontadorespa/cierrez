import os
import json
from background_worker import IntelligentWorker

def test_single_record(row_id):
    worker = IntelligentWorker()
    
    # 1. Fetch the record manually
    query = """
    SELECT row_id, imagen, imagen_header, imagen_ventas, imagen_visa_mc, imagen_clave, pos_visa_mc, pos_clave 
    FROM tblcierresz 
    WHERE row_id = %s;
    """
    records = worker.db.fetch_all(query, (row_id,))
    if not records:
        print(f"❌ Record {row_id} not found.")
        return
    
    record = records[0]
    print(f"🔍 Testing record: {record[0]}")
    
    # 2. Try to download images
    image_paths_in_db = record[1:6]
    local_paths = []
    
    for img_path in image_paths_in_db:
        if img_path:
            file_name = os.path.basename(img_path)
            print(f"📥 Attempting to download: {file_name}")
            local_path = worker.download_image(file_name)
            if local_path:
                print(f"✅ Downloaded to: {local_path}")
                local_paths.append(local_path)
            else:
                print(f"❌ Failed to download: {file_name}")

    if not local_paths:
        print("❌ No images downloaded. Worker would skip this record.")
        return

    # 3. Try AI processing
    print(f"🤖 Sending {len(local_paths)} images to AI...")
    extracted_data = worker.ai.process_cierre(local_paths)
    print(f"AI Response: {json.dumps(extracted_data, indent=2)}")

if __name__ == "__main__":
    test_single_record("4ab782a0")
