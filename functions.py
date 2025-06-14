import requests
import os




def download_image(url, save_dir="images", filename=None):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if filename is None:
        filename = url.split("/")[-1].split("?")[0]  # get file name from URL

    file_path = os.path.join(save_dir, filename)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # raise exception for bad status codes

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Image saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None


# download_image("https://replicate.delivery/xezq/pjDAr6Aect3KL6iMXepkErXYJTxMz1XOSvbncwuu85rswa2UA/tmpfzezdc1k.jpg", "images", "filename.jpg")