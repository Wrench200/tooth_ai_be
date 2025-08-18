# Custom Colors Feature Guide

## Overview

The `get_final_results` endpoint now supports custom color codes as an optional parameter. This allows you to override the previously generated brand identity colors with your own custom color palette when generating brand assets.

## API Endpoint

**POST** `/get_final_results`

## Request Parameters

### Required Parameters
- `userId` (string): User ID
- `brandId` (string): Brand ID
- `userName` (string): User's name
- `userEmail` (string): User's email

### Optional Parameters
- `userPhoneNumbers` (string): User's phone numbers
- `registrationNumber` (string): Business registration number
- `website` (string): Business website URL
- `brandLogo` (string): URL to brand logo
- `others` (object): Additional information
- `customColors` (object): **NEW** - Custom color palette

## Custom Colors Format

The `customColors` parameter accepts a dictionary with the following structure:

```json
{
  "primary_colors": [
    {
      "color_name": "Primary Blue",
      "hex_value": "#1E90FF",
      "description": "Main brand color for primary elements"
    },
    {
      "color_name": "Deep Blue",
      "hex_value": "#0066CC",
      "description": "Darker shade for emphasis"
    }
  ],
  "secondary_colors": [
    {
      "color_name": "Accent Orange",
      "hex_value": "#FF6B35",
      "description": "Accent color for calls-to-action"
    },
    {
      "color_name": "Light Gray",
      "hex_value": "#F5F5F5",
      "description": "Background color for subtle elements"
    }
  ],
  "brand_colors": [
    {
      "color_name": "Brand Green",
      "hex_value": "#28A745",
      "description": "Success and growth color"
    }
  ]
}
```

### Color Object Structure

Each color object should contain:
- `color_name` (string): Human-readable name for the color
- `hex_value` (string): Hex color code (e.g., "#1E90FF")
- `description` (string): Description of when/how to use this color

### Valid Color Keys

- `primary_colors`: Main brand colors used for primary elements
- `secondary_colors`: Supporting colors for secondary elements
- `brand_colors`: Additional brand-specific colors

## Example Usage

### Basic Request (No Custom Colors)
```json
{
  "userId": "user123",
  "brandId": "brand456",
  "userName": "John Doe",
  "userEmail": "john@example.com",
  "website": "https://example.com",
  "brandLogo": "https://example.com/logo.png"
}
```

### Request with Custom Colors
```json
{
  "userId": "user123",
  "brandId": "brand456",
  "userName": "John Doe",
  "userEmail": "john@example.com",
  "website": "https://example.com",
  "brandLogo": "https://example.com/logo.png",
  "customColors": {
    "primary_colors": [
      {
        "color_name": "Corporate Blue",
        "hex_value": "#2E86AB",
        "description": "Primary brand color for headers and main elements"
      },
      {
        "color_name": "Navy Blue",
        "hex_value": "#1B3B6F",
        "description": "Darker shade for text and emphasis"
      }
    ],
    "secondary_colors": [
      {
        "color_name": "Warm Orange",
        "hex_value": "#FF8C42",
        "description": "Accent color for buttons and highlights"
      },
      {
        "color_name": "Light Cream",
        "hex_value": "#F7F3E9",
        "description": "Background color for content areas"
      }
    ]
  }
}
```

## How It Works

1. **Color Override**: When `customColors` is provided, the system will override the colors from the previously generated brand identity with your custom colors.

2. **AI Generation**: The AI will use your custom colors when generating:
   - Brand patterns
   - Business cards
   - Letterheads
   - T-shirt mockups
   - Cap mockups
   - Signboards
   - All other brand assets

3. **Fallback**: If `customColors` is not provided or is null, the system will use the original colors from the brand identity.

## Validation Rules

The API validates the `customColors` parameter with the following rules:

1. **Type Check**: `customColors` must be a dictionary object
2. **Valid Keys**: Only `primary_colors`, `secondary_colors`, and `brand_colors` are allowed
3. **List Values**: Each color key must contain a list of color objects
4. **Color Object Structure**: Each color object should have `color_name`, `hex_value`, and `description`

## Error Responses

### Invalid Color Format
```json
{
  "success": false,
  "message": "customColors must be a dictionary object",
  "results": null
}
```

### Invalid Color Key
```json
{
  "success": false,
  "message": "Invalid color key: invalid_key. Valid keys are: primary_colors, secondary_colors, brand_colors",
  "results": null
}
```

### Invalid Color Value Type
```json
{
  "success": false,
  "message": "Color values must be lists. primary_colors is not a list.",
  "results": null
}
```

## Best Practices

1. **Color Harmony**: Ensure your custom colors work well together and follow color theory principles.

2. **Accessibility**: Consider contrast ratios for readability, especially for text colors.

3. **Brand Consistency**: Choose colors that align with your brand personality and target audience.

4. **Hex Format**: Always use 6-character hex codes (e.g., "#1E90FF" not "#1E90F").

5. **Descriptive Names**: Use clear, descriptive names for colors to help with brand guidelines.

## Integration Examples

### JavaScript/Fetch
```javascript
const response = await fetch('/get_final_results', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    userId: 'user123',
    brandId: 'brand456',
    userName: 'John Doe',
    userEmail: 'john@example.com',
    customColors: {
      primary_colors: [
        {
          color_name: 'Brand Blue',
          hex_value: '#1E90FF',
          description: 'Primary brand color'
        }
      ]
    }
  })
});

const result = await response.json();
```

### Python/Requests
```python
import requests

data = {
    'userId': 'user123',
    'brandId': 'brand456',
    'userName': 'John Doe',
    'userEmail': 'john@example.com',
    'customColors': {
        'primary_colors': [
            {
                'color_name': 'Brand Blue',
                'hex_value': '#1E90FF',
                'description': 'Primary brand color'
            }
        ]
    }
}

response = requests.post('/get_final_results', json=data)
result = response.json()
```

## Notes

- Custom colors are applied to all generated brand assets
- The original brand identity colors are preserved in the database
- Custom colors are only used for the current generation session
- All generated assets will reflect the custom color palette
- The system maintains backward compatibility - existing integrations will continue to work without modification
