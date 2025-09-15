
import sys
import os
import re
import chardet
import json
import shutil
import logging
import platformdirs
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QComboBox, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

class FileTracerPlus(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Tracer Plus: Your Ultimate File Search Companion")
        self.setGeometry(100, 100, 800, 600)
        self.file_search_results = {}

        # Determine application data directory
        app_name = "files"
        app_author = "FileTracerPlus" # Replace with actual author
        self.app_data_dir = platformdirs.user_data_dir(app_name, app_author)
        os.makedirs(self.app_data_dir, exist_ok=True)

        self.queries_file = os.path.join(self.app_data_dir, "search_queries.json")
        log_file_path = os.path.join(self.app_data_dir, "app.log")

        # Setup logging
        logging.basicConfig(filename=log_file_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.load_queries()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_label = QLineEdit("Select a directory to search...")
        self.dir_label.setReadOnly(True)
        dir_layout.addWidget(self.dir_label)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_button)
        layout.addLayout(dir_layout)

        # File search
        file_search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter file or folder name...")
        file_search_layout.addWidget(self.search_input)
        self.extension_input = QLineEdit()
        self.extension_input.setPlaceholderText("Filter by extensions, e.g., .txt, .py")
        file_search_layout.addWidget(self.extension_input)

        self.file_regex_checkbox = QCheckBox("Regex")
        file_search_layout.addWidget(self.file_regex_checkbox)

        self.file_search_button = QPushButton("Search Files")
        self.file_search_button.clicked.connect(self.start_file_search)
        file_search_layout.addWidget(self.file_search_button)
        layout.addLayout(file_search_layout)

        # Content search
        content_search_layout = QHBoxLayout()
        self.content_search_input = QLineEdit()
        self.content_search_input.setPlaceholderText("Enter text or regex to search in found files...")
        content_search_layout.addWidget(self.content_search_input)
        self.regex_checkbox = QCheckBox("Regex")
        content_search_layout.addWidget(self.regex_checkbox)
        self.content_search_button = QPushButton("Search Content")
        self.content_search_button.clicked.connect(self.start_content_search)
        content_search_layout.addWidget(self.content_search_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_results)
        content_search_layout.addWidget(self.clear_button)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_results)
        content_search_layout.addWidget(self.export_button)

        layout.addLayout(content_search_layout)

        # Filter options
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["None", "Size (KB) >", "Size (KB) <", "Date Modified (YYYY-MM-DD) >", "Date Modified (YYYY-MM-DD) <"])
        filter_layout.addWidget(self.filter_combo)

        self.filter_value_input = QLineEdit()
        self.filter_value_input.setPlaceholderText("Enter filter value")
        filter_layout.addWidget(self.filter_value_input)

        self.filter_button = QPushButton("Apply Filter")
        self.filter_button.clicked.connect(self.filter_displayed_results)
        filter_layout.addWidget(self.filter_button)
        layout.addLayout(filter_layout)

        # History and Saved Queries
        history_layout = QHBoxLayout()
        self.query_combo = QComboBox()
        self.query_combo.setPlaceholderText("Select a saved query")
        history_layout.addWidget(self.query_combo)
        self.update_query_combo()

        self.load_query_button = QPushButton("Load Query")
        self.load_query_button.clicked.connect(self.load_selected_query)
        history_layout.addWidget(self.load_query_button)

        self.save_query_button = QPushButton("Save Current")
        self.save_query_button.clicked.connect(self.save_current_query)
        history_layout.addWidget(self.save_query_button)

        self.delete_query_button = QPushButton("Delete Query")
        self.delete_query_button.clicked.connect(self.delete_selected_query)
        history_layout.addWidget(self.delete_query_button)

        layout.addLayout(history_layout)

        # Batch Operations
        batch_layout = QHBoxLayout()
        self.rename_button = QPushButton("Rename Selected")
        self.rename_button.clicked.connect(self.rename_selected_files)
        self.rename_button.setEnabled(False)
        batch_layout.addWidget(self.rename_button)

        self.copy_button = QPushButton("Copy Selected")
        self.copy_button.clicked.connect(self.copy_selected_files)
        self.copy_button.setEnabled(False)
        batch_layout.addWidget(self.copy_button)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_files)
        self.delete_button.setEnabled(False)
        batch_layout.addWidget(self.delete_button)

        layout.addLayout(batch_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Name", "Path", "Match"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSortingEnabled(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.update_batch_buttons_state)
        layout.addWidget(self.results_table)

        self.setLayout(layout)

        QTimer.singleShot(0, self.set_interactive_header)

    def set_interactive_header(self):
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_label.setText(directory)
            self.logger.info(f"Selected directory: {directory}")

    def start_file_search(self):
        search_path = self.dir_label.text()
        search_query = self.search_input.text()
        extensions = self.extension_input.text()
        use_file_regex = self.file_regex_checkbox.isChecked()

        if not os.path.isdir(search_path):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid directory to search.")
            self.logger.warning(f"Attempted file search with invalid directory: {search_path}")
            return

        self._perform_file_search_and_populate_results(search_path, search_query, extensions, use_file_regex)
        self.logger.info(f"File search initiated: Path='{search_path}', Query='{search_query}', Exts='{extensions}', Regex={use_file_regex}")
        self._display_nothing_found_message()

    def _perform_file_search_and_populate_results(self, search_path, search_query, extensions, use_file_regex):
        self.clear_results()
        allowed_extensions = [ext.strip() for ext in extensions.split(',') if ext.strip()]

        for root, dirs, files in os.walk(search_path):
            # Search files
            for name in files:
                match_found = False
                if use_file_regex:
                    try:
                        if re.search(search_query, name):
                            match_found = True
                    except re.error as e:
                        QMessageBox.warning(self, "Regex Error", f"Invalid regex pattern for file name: {e}")
                        self.logger.error(f"Invalid regex pattern for file name: {search_query} - {e}")
                        return # Stop search on invalid regex
                else:
                    if search_query.lower() in name.lower():
                        match_found = True

                if match_found:
                    if not allowed_extensions or any(name.endswith(ext) for ext in allowed_extensions):
                        file_path = os.path.join(root, name)
                        self.add_result_to_table(name, file_path)
                        self.file_search_results.append(file_path)

            # Search directories
            if not allowed_extensions:  # Only search directories if no extension filter is active
                for name in dirs:
                    match_found = False
                    if use_file_regex:
                        try:
                            if re.search(search_query, name):
                                match_found = True
                        except re.error as e:
                            QMessageBox.warning(self, "Regex Error", f"Invalid regex pattern for folder name: {e}")
                            self.logger.error(f"Invalid regex pattern for folder name: {search_query} - {e}")
                            return # Stop search on invalid regex
                    else:
                        if search_query.lower() in name.lower():
                            match_found = True

                    if match_found:
                        dir_path = os.path.join(root, name)
                        self.add_result_to_table(name, dir_path)
                        # We don't add directories to the file_search_results for content search

    def _get_all_files_in_directory(self, search_path):
        all_files = []
        for root, _, files in os.walk(search_path):
            for name in files:
                all_files.append(os.path.join(root, name))
        return all_files

    def start_content_search(self):
        search_path = self.dir_label.text()
        search_query = self.search_input.text()
        extensions = self.extension_input.text()
        use_file_regex = self.file_regex_checkbox.isChecked()
        content_query = self.content_search_input.text()
        use_content_regex = self.regex_checkbox.isChecked()

        if not os.path.isdir(search_path):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid directory to search.")
            self.logger.warning(f"Attempted content search with invalid directory: {search_path}")
            return

        if not content_query:
            QMessageBox.warning(self, "Missing Query", "Please enter a content search query.")
            self.logger.warning("Attempted content search with empty query.")
            return

        self.clear_results()

        # Determine the source of files for content search
        if search_query or extensions: # If file name/extension filters are active
            self._perform_file_search_and_populate_results(search_path, search_query, extensions, use_file_regex)
            files_to_search = self.file_search_results # Use results from file search
            self.logger.info("Content search initiated on filtered files.")
        else: # No file name/extension filters, search all files in directory
            files_to_search = self._get_all_files_in_directory(search_path)
            self.logger.info("Content search initiated on all files in directory.")

        new_results = []
        for file_path in files_to_search:
            name = os.path.basename(file_path)
            try:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] if result['encoding'] else 'utf-8'

                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if use_content_regex:
                            try:
                                if re.search(content_query, line):
                                    new_results.append((name, file_path, f"{i}: {line.strip()}"))
                            except re.error as e:
                                QMessageBox.warning(self, "Regex Error", f"Invalid regex pattern for content search: {e}")
                                self.logger.error(f"Invalid regex pattern for content search: {content_query} - {e}")
                                return # Stop search on invalid regex
                        else:
                            if content_query in line:
                                new_results.append((name, file_path, f"{i}: {line.strip()}"))
            except Exception as e:
                self.logger.error(f"Could not read file {file_path} for content search: {e}", exc_info=True)
                # QMessageBox.warning(self, "File Read Error", f"Could not read file {name}: {e}") # Too many popups

        self.results_table.setRowCount(0)
        for name, path, match in new_results:
            self.add_result_to_table(name, path, match)

        self._display_nothing_found_message()

    def _display_nothing_found_message(self):
        if self.results_table.rowCount() == 0:
            QMessageBox.information(self, "No Results", "No matching files or content found.")
            self.logger.info("No results found for the search.")

    def add_result_to_table(self, name, path, match=""):
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        self.results_table.setItem(row_position, 0, QTableWidgetItem(name))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(path))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(match))

    def clear_results(self):
        self.results_table.setRowCount(0)
        self.file_search_results = []

    def load_queries(self):
        try:
            if os.path.exists(self.queries_file):
                with open(self.queries_file, 'r') as f:
                    data = json.load(f)
                    self.search_queries = data.get("saved_queries", {})
                self.logger.info(f"Loaded queries from {self.queries_file}")
            else:
                self.search_queries = {}
                self.logger.info(f"No queries file found at {self.queries_file}. Initializing empty.")
        except Exception as e:
            self.logger.error(f"Error loading queries from {self.queries_file}: {e}", exc_info=True)
            QMessageBox.critical(self, "Load Error", f"Could not load saved queries: {e}")
            self.search_queries = {}

    def save_queries(self):
        try:
            data = {"saved_queries": self.search_queries}
            with open(self.queries_file, 'w') as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Saved queries to {self.queries_file}")
        except Exception as e:
            self.logger.error(f"Error saving queries to {self.queries_file}: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"Could not save queries: {e}")

    def update_query_combo(self):
        self.query_combo.clear()
        self.query_combo.addItem("Select a saved query")

        if self.search_queries:
            for query_name in self.search_queries.keys():
                self.query_combo.addItem(query_name)

    def save_current_query(self):
        query_name, ok = QInputDialog.getText(self, "Save Query", "Enter a name for this query:")
        if ok and query_name:
            try:
                self.search_queries[query_name] = {
                    "dir_path": self.dir_label.text(),
                    "search_input": self.search_input.text(),
                    "extension_input": self.extension_input.text(),
                    "file_regex_checkbox": self.file_regex_checkbox.isChecked(),
                    "content_search_input": self.content_search_input.text(),
                    "regex_checkbox": self.regex_checkbox.isChecked(),
                    "filter_combo": self.filter_combo.currentText(),
                    "filter_value_input": self.filter_value_input.text()
                }
                self.save_queries()
                self.update_query_combo()
                self.logger.info(f"Saved query: {query_name}")
            except Exception as e:
                self.logger.error(f"Error saving current query '{query_name}': {e}", exc_info=True)
                QMessageBox.critical(self, "Save Error", f"Could not save query: {e}")

    def load_selected_query(self):
        query_name = self.query_combo.currentText()
        if not query_name or query_name == "Select a saved query":
            return

        query_data = None
        try:
            if query_name in self.search_queries:
                query_data = self.search_queries[query_name]
                self.logger.info(f"Loading saved query: {query_name}")

            if query_data:
                self.dir_label.setText(query_data.get("dir_path", ""))
                self.search_input.setText(query_data.get("search_input", ""))
                self.extension_input.setText(query_data.get("extension_input", ""))
                self.file_regex_checkbox.setChecked(query_data.get("file_regex_checkbox", False))
                self.content_search_input.setText(query_data.get("content_search_input", ""))
                self.regex_checkbox.setChecked(query_data.get("regex_checkbox", False))
                self.filter_combo.setCurrentText(query_data.get("filter_combo", "None"))
                self.filter_value_input.setText(query_data.get("filter_value_input", ""))
        except Exception as e:
            self.logger.error(f"Error loading selected query '{query_name}': {e}", exc_info=True)
            QMessageBox.critical(self, "Load Error", f"Could not load query: {e}")

    def delete_selected_query(self):
        query_name = self.query_combo.currentText()
        if query_name and query_name != "Select a saved query" and query_name in self.search_queries:
            try:
                del self.search_queries[query_name]
                self.save_queries()
                self.update_query_combo()
                self.logger.info(f"Deleted saved query: {query_name}")
            except Exception as e:
                self.logger.error(f"Error deleting query '{query_name}': {e}", exc_info=True)
                QMessageBox.critical(self, "Delete Error", f"Could not delete query: {e}")

    def filter_displayed_results(self):
        filter_type = self.filter_combo.currentText()
        filter_value_str = self.filter_value_input.text()

        if filter_type == "None":
            for row in range(self.results_table.rowCount()):
                self.results_table.setRowHidden(row, False)
            self.logger.info("Filter reset to None.")
            return

        if not filter_value_str:
            QMessageBox.warning(self, "Missing Filter Value", "Please enter a value for the selected filter.")
            self.logger.warning(f"Attempted to apply filter '{filter_type}' with empty value.")
            return

        try:
            if "Size" in filter_type:
                filter_value = float(filter_value_str) * 1024 # Convert KB to bytes
            elif "Date Modified" in filter_type:
                filter_value = datetime.strptime(filter_value_str, "%Y-%m-%d")
            self.logger.info(f"Applying filter: Type='{filter_type}', Value='{filter_value_str}'")
        except ValueError:
            QMessageBox.warning(self, "Invalid Filter Value", "Please enter a valid number for size or YYYY-MM-DD for date.")
            self.logger.warning(f"Invalid filter value '{filter_value_str}' for filter type '{filter_type}'.")
            return

        for row in range(self.results_table.rowCount()):
            file_path = self.results_table.item(row, 1).text()
            if not os.path.isfile(file_path): # Only filter files, not directories
                self.results_table.setRowHidden(row, False)
                continue

            stat_info = os.stat(file_path)
            hide_row = False

            if "Size (KB) >" == filter_type:
                if stat_info.st_size <= filter_value:
                    hide_row = True
            elif "Size (KB) <" == filter_type:
                if stat_info.st_size >= filter_value:
                    hide_row = True
            elif "Date Modified (YYYY-MM-DD) >" == filter_type:
                file_mod_date = datetime.fromtimestamp(stat_info.st_mtime)
                if file_mod_date <= filter_value:
                    hide_row = True
            elif "Date Modified (YYYY-MM-DD) <" == filter_type:
                file_mod_date = datetime.fromtimestamp(stat_info.st_mtime)
                if file_mod_date >= filter_value:
                    hide_row = True

            self.results_table.setRowHidden(row, hide_row)

    def export_results(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Results", "",
                                                  "CSV Files (*.csv);;Text Files (*.txt)", options=options)
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as f:
                    if file_name.endswith('.csv'):
                        import csv
                        writer = csv.writer(f)
                        # Write header
                        header = [self.results_table.horizontalHeaderItem(i).text() for i in range(self.results_table.columnCount())]
                        writer.writerow(header)
                        # Write data
                        for row in range(self.results_table.rowCount()):
                            if not self.results_table.isRowHidden(row):
                                row_data = [self.results_table.item(row, col).text() if self.results_table.item(row, col) else ""
                                            for col in range(self.results_table.columnCount())]
                                writer.writerow(row_data)
                    else: # Text file
                        for row in range(self.results_table.rowCount()):
                            if not self.results_table.isRowHidden(row):
                                row_data = [self.results_table.item(row, col).text() if self.results_table.item(row, col) else ""
                                            for col in range(self.results_table.columnCount())]
                                f.write("\t".join(row_data) + "\n")
                self.logger.info(f"Exported results to {file_name}")
                QMessageBox.information(self, "Export Successful", f"Results exported to {file_name}")
            except Exception as e:
                self.logger.error(f"Error exporting results to {file_name}: {e}", exc_info=True)
                QMessageBox.critical(self, "Export Error", f"Could not export results: {e}")

    def update_batch_buttons_state(self):
        has_selection = len(self.results_table.selectedItems()) > 0
        self.rename_button.setEnabled(has_selection)
        self.copy_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def get_selected_file_paths(self):
        selected_paths = []
        for item in self.results_table.selectedItems():
            if item.column() == 1: # Path column
                selected_paths.append(item.text())
        return list(set(selected_paths)) # Return unique paths

    def rename_selected_files(self):
        selected_files = self.get_selected_file_paths()
        if not selected_files:
            return

        new_name_pattern, ok = QInputDialog.getText(self, "Rename Files",
                                                    "Enter new name pattern (use {name} for original name, {ext} for extension, {counter} for number):")
        if not ok or not new_name_pattern:
            self.logger.info("Rename operation cancelled by user or empty pattern provided.")
            return

        # Confirmation dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"You are about to rename {len(selected_files)} files. Are you sure?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.Cancel:
            self.logger.info("Rename operation cancelled by user at confirmation.")
            return

        for i, old_path in enumerate(selected_files):
            try:
                directory, old_filename = os.path.split(old_path)
                old_name, old_ext = os.path.splitext(old_filename)

                # Replace placeholders in the new name pattern
                new_filename = new_name_pattern.format(name=old_name, ext=old_ext.lstrip('.'), counter=i+1)
                new_path = os.path.join(directory, new_filename)

                os.rename(old_path, new_path)
                self.logger.info(f"Renamed: {old_path} -> {new_path}")
                # Update the table row with the new path
                for row in range(self.results_table.rowCount()):
                    if self.results_table.item(row, 1) and self.results_table.item(row, 1).text() == old_path:
                        self.results_table.setItem(row, 0, QTableWidgetItem(new_filename))
                        self.results_table.setItem(row, 1, QTableWidgetItem(new_path))
                        break
            except Exception as e:
                self.logger.error(f"Error renaming {old_path}: {e}", exc_info=True)
                QMessageBox.warning(self, "Rename Error", f"Could not rename {os.path.basename(old_path)}: {e}")

    def copy_selected_files(self):
        selected_files = self.get_selected_file_paths()
        if not selected_files:
            return

        destination_dir = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if not destination_dir:
            self.logger.info("Copy operation cancelled by user (no destination selected).")
            return

        # Confirmation dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"You are about to copy {len(selected_files)} files to {destination_dir}. Are you sure?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.Cancel:
            self.logger.info("Copy operation cancelled by user at confirmation.")
            return

        for file_path in selected_files:
            try:
                shutil.copy2(file_path, destination_dir)
                self.logger.info(f"Copied: {file_path} to {destination_dir}")
            except Exception as e:
                self.logger.error(f"Error copying {file_path} to {destination_dir}: {e}", exc_info=True)
                QMessageBox.warning(self, "Copy Error", f"Could not copy {os.path.basename(file_path)}: {e}")

    def delete_selected_files(self):
        selected_files = self.get_selected_file_paths()
        if not selected_files:
            return

        # Confirmation dialog - VERY IMPORTANT FOR DELETE
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(f"<p><b>WARNING:</b> You are about to permanently delete {len(selected_files)} files/folders.</p>"\
                        "<p>This action cannot be undone. Are you absolutely sure?</p>")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.No:
            self.logger.info("Delete operation cancelled by user at confirmation.")
            return

        for file_path in selected_files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.logger.info(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    self.logger.info(f"Deleted directory: {file_path}")
                # Remove the row from the table
                for row in range(self.results_table.rowCount()):
                    if self.results_table.item(row, 1) and self.results_table.item(row, 1).text() == file_path:
                        self.results_table.removeRow(row)
                        break
            except Exception as e:
                self.logger.error(f"Error deleting {file_path}: {e}", exc_info=True)
                QMessageBox.critical(self, "Delete Error", f"Could not delete {os.path.basename(file_path)}: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = FileTracerPlus()
    main_win.show()
    sys.exit(app.exec())
