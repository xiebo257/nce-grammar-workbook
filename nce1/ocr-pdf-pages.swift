import AppKit
import PDFKit
import Vision

guard CommandLine.arguments.count >= 4,
      let firstPage = Int(CommandLine.arguments[2]),
      let lastPage = Int(CommandLine.arguments[3]),
      let document = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1])) else {
  fputs("Usage: ocr-pdf-pages <pdf-path> <first-page> <last-page>\n", stderr)
  exit(2)
}

for pageNumber in firstPage...lastPage {
  guard let page = document.page(at: pageNumber - 1) else { continue }
  let bounds = page.bounds(for: .mediaBox)
  let scale = max(1, 1800 / bounds.width)
  let image = page.thumbnail(of: NSSize(width: bounds.width * scale, height: bounds.height * scale), for: .mediaBox)
  guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
  let request = VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.usesLanguageCorrection = true
  request.recognitionLanguages = ["en-US"]
  try VNImageRequestHandler(cgImage: cgImage).perform([request])
  let text = (request.results ?? [])
    .compactMap { $0.topCandidates(1).first?.string }
    .joined(separator: "\n")
  print("===== PDF PAGE \(pageNumber) =====")
  print(text)
}
