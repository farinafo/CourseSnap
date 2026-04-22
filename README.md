# CourseSnap

CourseSnap is a Windows desktop tool designed to help students efficiently capture course slides, generate PDFs, and create AI-powered study notes.

## Language

- English version available in Releases
- 中文版本见 Releases（Chinese version available in Releases）

## Features

- 📸 Capture slides during online courses
- 📄 Automatically generate structured PDFs from captured images
- 🤖 Create AI-powered summaries based on transcripts
- 🗂 Organize course content into project folders

## Download

Download the latest Windows release from the **Releases** page.  
Both English and Chinese versions are available.

## How to Use

1. Download and extract the release zip
2. Run `app.exe`
3. Click **Start Recording** to create a course project and capture slides
4. Click **Generate PDF** to convert captured slides into a PDF
5. Place a `.txt` or `.docx` transcript file into the project folder
6. Click **Summarize** and enter your own API key (from Alibaba Cloud DashScope / Tongyi Qianwen)

## File Structure

Make sure all files remain in the same folder after extraction. The main application depends on these companion executables:

- `capture.exe`
- `make_pdf.exe`
- `summarize.exe`

## Notes & Security

- Do not share any `config.json` file that contains a real API key
- This project is intended for personal learning and productivity use

## Author

Chen Fan
