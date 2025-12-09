import { parseManuscriptContent, type SurveySummary } from './manuscriptParser'

/**
 * Utility for loading and parsing content from manuscript-first-submission.docx
 * 
 * The manuscript has been extracted to public/manuscript/content.html and content.txt
 */

export interface ManuscriptContent {
  background: string
  methods: string
  references: string
  summary: SurveySummary | null
}

/**
 * Loads content from the extracted manuscript files
 * @returns Promise resolving to parsed manuscript content
 */
export async function loadManuscriptContent(): Promise<ManuscriptContent> {
  try {
    // Load the extracted text content
    const textResponse = await fetch('/manuscript/content.txt')
    const text = await textResponse.text()
    
    // Parse the content to extract structured information
    const summary = parseManuscriptContent(text)
    
    // Extract sections from the text
    const background = extractSection(text, 'Introduction', 'Materials and methods')
    const methods = extractSection(text, 'Materials and methods', 'Results')
    const references = extractSection(text, 'References', 'Figures')
    
    return {
      background: formatSection('Background', background),
      methods: formatSection('Methods', methods),
      references: formatSection('References', references),
      summary
    }
  } catch (error) {
    console.error('Failed to load manuscript content:', error)
    return {
      background: '<p>Failed to load background content.</p>',
      methods: '<p>Failed to load methods content.</p>',
      references: '<p>Failed to load references content.</p>',
      summary: null
    }
  }
}

function extractSection(text: string, startMarker: string, endMarker: string): string {
  const startIndex = text.indexOf(startMarker)
  const endIndex = text.indexOf(endMarker)
  
  if (startIndex === -1) return ''
  if (endIndex === -1) return text.substring(startIndex)
  
  return text.substring(startIndex, endIndex).trim()
}

function formatSection(title: string, content: string): string {
  if (!content) return `<h3>${title}</h3><p>Content not available.</p>`
  
  // Convert plain text to HTML with basic formatting
  const html = content
    .split('\n')
    .filter(line => line.trim().length > 0)
    .map(line => {
      // Skip very short lines that are likely headers or metadata
      if (line.trim().length < 10) return ''
      return `<p>${line.trim()}</p>`
    })
    .filter(line => line.length > 0)
    .join('\n')
  
  return `<h3>${title}</h3>\n${html}`
}

/**
 * Extracts a specific section from the manuscript
 * @param content - The full manuscript content
 * @param section - The section to extract
 * @returns The HTML content for the requested section
 */
export function getManuscriptSection(
  content: ManuscriptContent,
  section: 'background' | 'methods' | 'references'
): string {
  return content[section] || ''
}

