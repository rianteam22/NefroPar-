import json
import logging
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import pandas as pd
from unstract.llmwhisperer.client_v2 import LLMWhispererClientException
from unstract.llmwhisperer import LLMWhispererClientV2
import PyPDF2
import re
from difflib import SequenceMatcher

def save_extracted_text(text, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    logging.info(f"Saved extracted text to {file_path}")

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Saved structured data to {file_path}")

def create_directories(paths):
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def extract_text_from_pdf(file_path, pages_list=None):
    llmw = LLMWhispererClientV2()
    try:
        result = llmw.whisper(
            wait_for_completion=True,
            wait_timeout=200,
            file_path=file_path, 
            pages_to_extract=pages_list
        )
        extracted_text = result["extraction"]["result_text"]
        logging.info(f"Extracted text from PDF: {file_path}")
        return extracted_text
    except LLMWhispererClientException as e:
        logging.error(f"Failed to extract text from PDF {file_path}: {e}")
        raise RuntimeError(f"Error extracting text from PDF {file_path}: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error extracting text from PDF {file_path}: {e}")
        raise RuntimeError(f"Unexpected error extracting text from PDF {file_path}: {e}")

def converter_pdf_para_png_com_preprocessamento(pdf_path, output_dir):
    """
    Converte cada página de um PDF em imagens PNG, aplica pré-processamento para melhorar a qualidade do OCR
    e salva as imagens em um diretório específico.

    :param pdf_path: Caminho para o arquivo PDF.
    :param output_dir: Diretório onde as imagens PNG serão salvas.
    """
    try:
        # Converte o PDF em uma lista de imagens
        paginas = convert_from_path(pdf_path, dpi=400)
        
        # Cria o diretório de saída se não existir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, pagina in enumerate(paginas):
            # Converte para escala de cinza
            imagem = pagina.convert('L')
            
            # Aumenta o contraste
            enhancer = ImageEnhance.Sharpness(imagem)
            imagem = enhancer.enhance(1.0)  # Ajuste o fator conforme necessário
            
            # Aplica filtro de nitidez
            imagem = imagem.filter(ImageFilter.DETAIL)
            
            # Binariza a imagem
            imagem = imagem.point(lambda x: 0 if x < 128 else 255, '1')
            
            # Salva a imagem processada como PNG
            imagem_path = output_dir / f"pagina_{i + 1}.png"
            imagem.save(imagem_path, 'PNG')
            logging.info(f"Página {i + 1} salva como {imagem_path}")
    
    except Exception as e:
        logging.error(f"Erro ao converter {pdf_path} para imagens PNG: {e}")

def json_to_csv(json_file_path, csv_file_path):
    """
    Converte um arquivo JSON para um DataFrame CSV e o salva no caminho especificado.

    :param json_file_path: Caminho para o arquivo JSON.
    :param csv_file_path: Caminho onde o arquivo CSV será salvo.
    """
    try:
        # Carrega os dados do JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Converte os dados JSON para um DataFrame
        df = pd.json_normalize(json_data)
        
        # Salva o DataFrame em um arquivo CSV
        df.to_csv(csv_file_path, index=False, encoding='utf-8')
        logging.info(f"Successfully converted {json_file_path} to {csv_file_path}")

    except Exception as e:
        logging.error(f"Failed to convert {json_file_path} to CSV: {e}")
        raise

def json_to_unified_csv(json_dir, unified_csv_path):
    """
    Combina múltiplos arquivos JSON em um diretório em um único arquivo CSV.

    :param json_dir: Diretório contendo os arquivos JSON.
    :param unified_csv_path: Caminho onde o arquivo CSV unificado será salvo.
    """
    try:
        # Lista para armazenar cada DataFrame
        dataframes = []

        # Itera por todos os arquivos .json no diretório especificado
        for json_file in Path(json_dir).glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Converte os dados JSON para um DataFrame
            df = pd.json_normalize(json_data)
            dataframes.append(df)

        # Concatena todos os DataFrames em um único DataFrame
        unified_df = pd.concat(dataframes, ignore_index=True)

        # Salva o DataFrame unificado em um arquivo CSV
        unified_df.to_csv(unified_csv_path, index=False, encoding='utf-8')
        logging.info(f"Unified CSV file created at {unified_csv_path}")

    except Exception as e:
        logging.error(f"Failed to create unified CSV file: {e}")
        raise

def extract_text_from_pdf_direct(pdf_path):
    """
    Extract text directly from a PDF file without OCR.
    
    :param pdf_path: Path to the PDF file.
    :return: Extracted text as a string.
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        
        logging.info(f"Extracted text directly from PDF: {pdf_path}")
        return text
    except Exception as e:
        logging.error(f"Failed to extract text directly from PDF {pdf_path}: {e}")
        raise RuntimeError(f"Error extracting text directly from PDF {pdf_path}: {e}")

def find_matching_lab_result(patient_name, lab_dir):
    """
    Find a lab result PDF file that matches the patient name using fuzzy matching.
    
    :param patient_name: Name of the patient to search for.
    :param lab_dir: Directory containing lab result PDFs.
    :return: Path to the matching PDF file, or None if no match is found.
    """
    try:
        lab_dir_path = Path(lab_dir)
        if not lab_dir_path.exists():
            logging.warning(f"Lab results directory does not exist: {lab_dir}")
            return None
        
        best_match = None
        best_score = 0.0
        threshold = 0.7  # Similarity threshold
        
        # Normalize patient name for comparison
        patient_name = patient_name.lower().strip()
        
        for pdf_file in lab_dir_path.glob('*.pdf'):
            # Extract filename without extension for comparison
            filename = pdf_file.stem.lower()
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, patient_name, filename).ratio()
            
            if similarity > threshold and similarity > best_score:
                best_score = similarity
                best_match = pdf_file
        
        if best_match:
            logging.info(f"Found matching lab result for {patient_name}: {best_match} (score: {best_score:.2f})")
            return best_match
        else:
            logging.warning(f"No matching lab result found for {patient_name}")
            return None
    
    except Exception as e:
        logging.error(f"Error finding matching lab result for {patient_name}: {e}")
        return None

def extract_patient_name_from_text(text):
    """
    Extract patient name from the OCR text.
    
    :param text: OCR text from the patient form.
    :return: Patient name as a string or None if not found.
    """
    try:
        # Look for patterns that might indicate a name
        # This is a simple approach and may need adjustment based on actual form structure
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Look for lines that might contain the patient name
            # Check for typical field labels
            if re.search(r'Nome\s+do\s+participante|Nome\s+paciente|Paciente|Nome\s+completo', line, re.IGNORECASE):
                # The name might be in the same line after a colon or in the next line
                if ':' in line:
                    return line.split(':', 1)[1].strip()
                elif i + 1 < len(lines):
                    return lines[i + 1].strip()
            
            # Try to find all-caps names that are typically patient identifiers
            if line and line.strip() and line.isupper() and len(line.split()) >= 2:
                return line.strip()
        
        # If no clear patient name field is found, look for an all-caps line that could be a name
        for line in lines:
            if line and line.strip() and len(line.split()) >= 2 and not re.search(r'\d', line):
                # Heuristic: lines with 2+ words, no digits, might be names
                return line.strip()
        
        return None
    except Exception as e:
        logging.error(f"Error extracting patient name from text: {e}")
        return None

def combine_form_and_lab_data(form_text, lab_text):
    """
    Combine form data and lab data for processing.
    
    :param form_text: Text extracted from the patient form.
    :param lab_text: Text extracted from the lab results.
    :return: Combined text for processing.
    """
    combined_text = "=== PATIENT FORM DATA ===\n\n"
    combined_text += form_text
    combined_text += "\n\n=== LABORATORY RESULTS ===\n\n"
    combined_text += lab_text if lab_text else "No laboratory results found."
    return combined_text
