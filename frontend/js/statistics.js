/* ============================================
   STATISTICS TRACKER
   ============================================ */

function updateWordCount(quill, elementId) {
    const text = quill.getText().trim();
    const words = text ? text.split(/\s+/).length : 0;
    const el = document.getElementById(elementId);
    if (el) el.textContent = words;
    return words;
}

function updateCharacterCount(quill, elementId) {
    const text = quill.getText();
    const chars = text.length;
    const el = document.getElementById(elementId);
    if (el) el.textContent = chars;
    return chars;
}

function getDocumentStats(quill) {
    const text = quill.getText().trim();
    const words = text ? text.split(/\s+/).length : 0;
    const chars = text.length;
    const paragraphs = text ? text.split(/\n/).filter(p => p.trim()).length : 0;
    
    return { words, chars, paragraphs };
}
