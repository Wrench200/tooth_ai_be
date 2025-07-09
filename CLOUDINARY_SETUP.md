# Cloudinary Integration Setup

## Overview
Your ToothAI application now uses Cloudinary for cloud-based image storage instead of storing images locally. This provides better scalability, faster image delivery, and automatic CDN optimization.

## What's Changed

### 1. New Files Created
- **`cloudinary_utils.py`**: Utility functions for Cloudinary operations
- **`test_cloudinary.py`**: Test script to verify Cloudinary integration
- **`CLOUDINARY_SETUP.md`**: This documentation file

### 2. Updated Files
- **`requirements.txt`**: Added `cloudinary` dependency
- **`db.py`**: Added `answer_images` table and image management functions
- **`main.py`**: Added Cloudinary endpoints for image operations
- **`imagen.py`**: Updated to automatically upload to Cloudinary
- **`results.py`**: Updated logo generation to use Cloudinary

## Setup Instructions

### 1. Install Dependencies
```bash
# If using pip
pip install cloudinary

# If using uv
uv add cloudinary

# If using conda
conda install -c conda-forge cloudinary
```

### 2. Configure Environment Variables
Add these to your `.env` file:
```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 3. Get Cloudinary Credentials
1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Go to your Dashboard
3. Copy your Cloud Name, API Key, and API Secret

## New API Endpoints

### Generate and Upload Image
```http
POST /generate_and_upload_image
Content-Type: application/json

{
    "prompt": "Your image prompt",
    "answerId": "uuid",
    "section": 1,
    "question": 1,
    "userId": "uuid"
}
```

### Get Image URL
```http
POST /get_image
Content-Type: application/json

{
    "answerId": "uuid",
    "section": 1,
    "question": 1,
    "userId": "uuid"
}
```

### Delete Image
```http
POST /delete_image
Content-Type: application/json

{
    "answerId": "uuid",
    "section": 1,
    "question": 1,
    "userId": "uuid"
}
```

### Get All Images for Answer
```http
POST /get_all_images
Content-Type: application/json

{
    "answerId": "uuid",
    "userId": "uuid"
}
```

## Database Changes

### New Table: `answer_images`
```sql
CREATE TABLE answer_images (
    imageId SERIAL PRIMARY KEY,
    answerId_fk UUID NOT NULL,
    section_number INT NOT NULL,
    question_number INT NOT NULL,
    cloudinary_url TEXT NOT NULL,
    cloudinary_public_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (answerId_fk) REFERENCES answers_main(answerId) ON DELETE CASCADE,
    UNIQUE (answerId_fk, section_number, question_number)
);
```

## Testing

Run the test script to verify everything works:
```bash
python test_cloudinary.py
```

## Benefits

1. **Scalability**: No local storage limits
2. **Performance**: CDN-optimized image delivery
3. **Reliability**: Cloudinary's 99.9% uptime SLA
4. **Cost-effective**: Pay only for what you use
5. **Automatic optimization**: Images are automatically optimized for different devices

## Image Organization

Images are organized in Cloudinary with the following structure:
- **Folder**: `toothai/`
- **Answer images**: `toothai/{answerId}/section_{section}_question_{question}`
- **Logo images**: `toothai/{brandId}/logo_{number}`

## Error Handling

The system includes comprehensive error handling:
- Connection failures
- Upload failures
- Database transaction failures
- User authorization checks

## Security

- All endpoints verify user ownership of answers
- Images are stored with secure URLs
- Public IDs are structured to prevent conflicts 