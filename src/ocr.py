from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    engine="transformers",
)

result = ocr.predict('data/raw/test.png')
for res in result:
    res.print()
    res.save_to_json("data/ocr")