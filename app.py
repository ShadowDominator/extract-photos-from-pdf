import os
import gradio as gr
from pdf2image import convert_from_path,pdfinfo_from_path
import zipfile

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))



DIRECTORY = "image_reference"
DIRECTORY_OUTPUT = "output"
DIRECTORIES = [DIRECTORY, DIRECTORY_OUTPUT]

# Check and create directories
for directory in DIRECTORIES:
    if not os.path.exists(directory):
        os.makedirs(directory)        
    else:
        pass


ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
def get_image_files(directory):
    image_files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
            filepath = os.path.join(directory, filename)
            image_files.append(filepath)
    return image_files


def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")



def extract_photos_from_pdf(file_pdf):    
    clear_directory(DIRECTORY)   
    clear_directory(DIRECTORY_OUTPUT)     
    try:
        pdf_path = file_pdf.name
        info = pdfinfo_from_path(pdf_path, userpw=None, poppler_path=None)

        total_pages = info["Pages"]  # Total number of pages in the PDF book
        batch_size = 100  # Number of pages to process in each batch

        for start_page in range(0, total_pages, batch_size):
            end_page = min(start_page + batch_size, total_pages)
            images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)
            for idx, image in enumerate(images, start=start_page):
                image.save(f'{DIRECTORY}/{idx+1}.png', 'PNG')

        images_pdf_list = get_image_files(DIRECTORY)
        image_names = [(path, os.path.basename(path)) for path in images_pdf_list]         
        sorted_names = sorted(image_names, key=lambda x: int(x[1].split('.')[0]))               
        zip_folder(DIRECTORY, f'{DIRECTORY_OUTPUT}/all_photos.zip') 
        return (
            gr.Gallery.update(value=sorted_names, label=f"Detected {len(images_pdf_list)} Page{'' if len(images_pdf_list) == 1 else 's'}", show_label=True, visible=True),
            gr.File.update(value=f'{DIRECTORY_OUTPUT}/all_photos.zip',visible=True)
        )
    except:     
        return (
            gr.Gallery.update(value=[], label="Error", show_label=True, visible=True),
            gr.File.update(visible=False)
        )
         
with gr.Blocks() as demo:
    with gr.Tabs() as tabs:        

        with gr.TabItem("PDF",id=0):

            with gr.Row():
                with gr.Column():   
                    proegres = gr.Text(show_label=False,value="",visible=False)                        
                    file_pdf = gr.File(file_types=['.pdf'], label="Upload PDF *")           
                    btn = gr.Button("Extract Photos from PDF")  
                    

    with gr.Tabs(visible=True) as tabs_under:
   
        with gr.TabItem("Photos",id=0):

            with gr.Column():
                
                list_image = gr.Gallery(value=[], label=f"0 Page",visible=True, show_label=True, elem_id="gallery").style(columns=[3], object_fit="cover", height="auto")
                file_download = gr.File(file_types=['.zip'], label="Download File",visible=False) 


    examples = gr.Examples([["./1706.03762.pdf", None]], fn=extract_photos_from_pdf,inputs=[file_pdf],outputs=[list_image,file_download], cache_examples=False)    
    btn.click(fn=extract_photos_from_pdf,inputs=[file_pdf],outputs=[list_image,file_download])



                
demo.queue().launch()