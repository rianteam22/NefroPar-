from config import configure_logging, load_environment
from process import process_medical_information, process_screening_data
from utils import (
    create_directories, save_extracted_text, save_json, extract_text_from_pdf, 
    extract_text_from_pdf_direct, find_matching_lab_result, extract_patient_name_from_text,
    combine_form_and_lab_data
)
from pathlib import Path
import logging
import os

def process_screening_form(form_file, txt_dir, json_dir, lab_dir, csv_dir=None):
    """
    Process a screening form PDF and find matching lab results.
    
    :param form_file: Path to the screening form PDF
    :param txt_dir: Directory to save extracted text
    :param json_dir: Directory to save JSON data
    :param lab_dir: Directory containing lab result PDFs
    :param csv_dir: Optional directory to save CSV data
    """
    base_name = form_file.stem
    try:
        # Extract text from the screening form using OCR
        form_text = extract_text_from_pdf(str(form_file))
        save_extracted_text(form_text, txt_dir / f"{base_name}_form.txt")
        
        # Extract patient name from the form text
        patient_name = extract_patient_name_from_text(form_text)
        if not patient_name:
            logging.warning(f"Could not extract patient name from {form_file.name}")
            lab_text = None
        else:
            # Find matching lab result
            lab_file = find_matching_lab_result(patient_name, lab_dir)
            if lab_file:
                # Extract text directly from the lab PDF (no OCR)
                lab_text = extract_text_from_pdf_direct(lab_file)
                save_extracted_text(lab_text, txt_dir / f"{base_name}_lab.txt")
            else:
                lab_text = None
                logging.warning(f"No matching lab result found for {patient_name}")
        
        # Combine form and lab data
        combined_text = combine_form_and_lab_data(form_text, lab_text)
        save_extracted_text(combined_text, txt_dir / f"{base_name}_combined.txt")
        
        # Process the combined data
        structured_data = process_screening_data(form_text, lab_text)
        save_json(structured_data, json_dir / f"{base_name}.json")
        
        # Optionally convert to CSV
        if csv_dir:
            from utils import json_to_csv
            csv_file = csv_dir / f"{base_name}.csv"
            json_to_csv(json_dir / f"{base_name}.json", csv_file)
        
        logging.info(f"Successfully processed {form_file.name}")
        
    except Exception as e:
        logging.error(f"Failed to process {form_file.name}: {e}")

def main():
    load_environment()
    configure_logging()
    
    logging.info("Starting script execution.")
    
    # Create necessary directories
    pdf_dir = Path('scans/screening_forms')
    lab_dir = Path('scans/lab_results')
    txt_dir = Path('scans/txt')
    json_dir = Path('scans/json')
    csv_dir = Path('scans/csv')
    
    create_directories([pdf_dir, lab_dir, txt_dir, json_dir, csv_dir])
    
    # Process all screening forms in the directory
    for form_file in pdf_dir.glob('*.pdf'):
        process_screening_form(form_file, txt_dir, json_dir, lab_dir, csv_dir)
    
    # Optionally create a unified CSV from all JSON files
    from utils import json_to_unified_csv
    unified_csv_path = csv_dir / "all_screenings.csv"
    json_to_unified_csv(json_dir, unified_csv_path)
    
    logging.info("Script execution completed.")

if __name__ == "__main__":
    main()
