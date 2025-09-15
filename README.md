# File Tracer Plus: Your Ultimate File Search Companion

File Tracer Plus is a powerful and intuitive desktop application designed to help you efficiently search, filter, and manage files within your system. Built with Python and PyQt6, it offers a comprehensive set of tools for both basic and advanced file operations.

## Features

*   **Recursive File and Folder Search:** Quickly locate files and folders by name within a specified directory and its subdirectories.
*   **File Extension Filter:** Refine your searches by specifying one or more file extensions (e.g., `.txt, .py, .md`).
*   **Content Search (Text & Regex):** Search inside files for specific plain text or complex regular expression patterns. Results display the matching lines.
*   **Regex Support for File/Folder Names:** Use regular expressions for more flexible matching of file and folder names.
*   **Search Filtering:** Filter displayed results by file size (greater than/less than) and modification date (after/before).
*   **Results Sorting:** Sort search results by Name, Path, or Match column by clicking on the table headers.
*   **Search History & Saved Queries:** Automatically saves your recent searches to history and allows you to save frequently used queries for quick reuse.
*   **Batch Operations:** Perform bulk actions on selected files:
    *   **Rename:** Rename multiple files using a pattern with placeholders (`{name}`, `{ext}`, `{counter}`).
    *   **Copy:** Copy selected files to a specified destination directory.
    *   **Delete:** Permanently delete selected files or folders with a strong confirmation warning.
*   **Export Results:** Export your search results (including Name, Path, and Match) to a CSV or plain text file.

## Installation

To get started with File Tracer Plus, you need to have Python installed on your system. Then, you can install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

1.  **Run the Application:**
    ```bash
    python main.py
    ```

2.  **Select Directory:** Click the "Browse" button to choose the root directory for your search.

3.  **Search Files/Folders:**
    *   Enter a name or pattern in the "Enter file or folder name..." field.
    *   Optionally, enter extensions (e.g., `.py, .txt`) in the "Filter by extensions..." field.
    *   Check "Regex" if your name/pattern is a regular expression.
    *   Click "Search Files" to populate the results table.

4.  **Search Content:**
    *   (Optional) After performing a file search, enter text or a regex pattern in the "Enter text or regex to search in found files..." field.
    *   Check "Regex" if your content search is a regular expression.
    *   Click "Search Content" to filter the currently displayed files by their content.

5.  **Filter Results:**
    *   Use the "Filter options" dropdown to select criteria like "Size (KB) >" or "Date Modified (YYYY-MM-DD) <".
    *   Enter a value in the "Enter filter value" field.
    *   Click "Apply Filter" to hide rows that don't match.

6.  **Sort Results:** Click on the column headers (Name, Path, Match) in the results table to sort the data.

7.  **History and Saved Queries:**
    *   Use the dropdown to load a previous search saved query.
    *   Click "Save Current" to save your current search parameters with a custom name.
    *   Click "Delete Query" to remove a saved query or history item.

8.  **Batch Operations:**
    *   Select one or more rows in the results table.
    *   Click "Rename Selected", "Copy Selected", or "Delete Selected" and follow the prompts.

9.  **Export Results:** Click the "Export" button to save the currently displayed results to a CSV or text file.

## Technologies Used

*   **Python:** The core programming language.
*   **PyQt6:** For building the graphical user interface.
*   **`os` & `shutil`:** For file system operations.
*   **`re`:** For regular expression matching.
*   **`chardet`:** For character encoding detection when reading file content.
*   **`json`:** For saving and loading search queries and history.
*   **`datetime`:** For date-based filtering.

## Future Enhancements

*   **Progress Indicators:** Display progress bars for long-running operations (e.g., content search).
*   **Error Handling Improvements:** More user-friendly error messages and dialogs.
*   **Advanced Batch Operations:** More sophisticated renaming patterns, moving files, etc.
*   **Configuration Options:** Allow users to customize history size, default search paths, etc.
*   **Performance Optimizations:** Further optimize content search for very large files or directories.
