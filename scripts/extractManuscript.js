import mammoth from 'mammoth'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const manuscriptPath = path.join(__dirname, '..', 'manuscript-first-submission.docx')
const outputDir = path.join(__dirname, '..', 'public', 'manuscript')
const imagesDir = path.join(outputDir, 'images')

// Ensure output directories exist
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true })
}
if (!fs.existsSync(imagesDir)) {
  fs.mkdirSync(imagesDir, { recursive: true })
}

async function extractManuscript() {
  try {
    console.log('Reading manuscript file...')
    const result = await mammoth.convertToHtml(
      { path: manuscriptPath },
      {
        convertImage: mammoth.images.imgElement((image) => {
          return image.read('base64').then((imageBuffer) => {
            const imageExtension = image.contentType.split('/')[1] || 'png'
            const imageName = `figure-${Date.now()}-${Math.random().toString(36).substr(2, 9)}.${imageExtension}`
            const imagePath = path.join(imagesDir, imageName)
            
            // Save image
            fs.writeFileSync(imagePath, imageBuffer, 'base64')
            
            // Return image element
            return {
              src: `/manuscript/images/${imageName}`
            }
          })
        })
      }
    )

    // Also get text for easier parsing
    const textResult = await mammoth.extractRawText({ path: manuscriptPath })

    // Save HTML
    fs.writeFileSync(
      path.join(outputDir, 'content.html'),
      result.value
    )

    // Save raw text
    fs.writeFileSync(
      path.join(outputDir, 'content.txt'),
      textResult.value
    )

    // Save messages (warnings, etc.)
    if (result.messages.length > 0) {
      fs.writeFileSync(
        path.join(outputDir, 'messages.json'),
        JSON.stringify(result.messages, null, 2)
      )
    }

    console.log('Extraction complete!')
    console.log(`- HTML saved to: ${path.join(outputDir, 'content.html')}`)
    console.log(`- Text saved to: ${path.join(outputDir, 'content.txt')}`)
    console.log(`- Images saved to: ${imagesDir}`)
    console.log(`- Found ${result.messages.length} messages/warnings`)

    return {
      html: result.value,
      text: textResult.value,
      messages: result.messages
    }
  } catch (error) {
    console.error('Error extracting manuscript:', error)
    throw error
  }
}

extractManuscript()

