# Question Management Redesign - Feature Documentation

## Overview
Complete redesign of the question management system with support for HTML formatting, multiple media files, and a modern user interface. This update transforms the question creation experience from a simple form to a powerful content management system.

## Key Features

### 1. **HTML Editor Integration**
- **WYSIWYG Editor**: TinyMCE integration for rich text editing
- **HTML Support**: Full HTML formatting in question text
- **Formatting Options**:
  - Text formatting (bold, italic, underline, colors)
  - Lists (ordered and unordered)
  - Tables
  - Links
  - Code blocks
  - Images (inline)
  - Alignment options

### 2. **Multiple Media Files**
- **Unlimited Attachments**: Add multiple media files to each question
- **Supported Types**:
  - Images (JPG, PNG, GIF, WebP)
  - Videos (MP4, WebM, AVI)
  - Audio (MP3, WAV, OGG)
  - Documents (PDF)
- **Media Features**:
  - Captions for each media file
  - Display order control
  - Type badges (visual indicators)
  - Preview thumbnails
  - Easy deletion

### 3. **Redesigned Interface**

#### **List View** (`manage_questions.html`)
- **Comprehensive Table**: All questions in a sortable table
- **Columns**:
  - Question Number
  - Type (with colored badges)
  - Question Text Preview
  - Answer
  - Points
  - Media Files Count
  - Clues Count
  - Actions (Edit, Manage Clues, Delete)
- **Statistics Dashboard**:
  - Total Questions
  - Total Media Files
  - Total Clues
  - Total Points
- **Empty State**: Friendly message when no questions exist

#### **Add/Edit View** (`add_edit_question.html`)
- **Two-Column Layout**:
  - Left: Question details and media
  - Right: Quick actions and help
- **Sections**:
  - Question Details (number, type, points, text, answer)
  - Media Files (existing + new)
  - Actions (save, cancel)
  - Help (contextual guidance)

### 4. **Points System**
- **Configurable Points**: Each question can have different point values
- **Default**: 10 points per question
- **Display**: Shown in list view with star icon
- **Total**: Calculated in statistics

### 5. **Question Types**
- **Text Only**: No media attachments
- **Image**: Questions with images
- **Video**: Questions with videos
- **Mixed Media**: Multiple media types

## Database Changes

### New Model: `QuestionMedia`
```python
class QuestionMedia(db.Model):
    id = Integer (Primary Key)
    question_id = Integer (Foreign Key)
    media_type = String(20)  # image, video, audio, document
    media_url = String(500)
    media_caption = String(255)
    display_order = Integer
    created_at = DateTime
```

### Updated Model: `Question`
```python
class Question(db.Model):
    # Existing fields...
    points = Integer (NEW)
    updated_at = DateTime (NEW)
    
    # New relationship
    media_files = relationship('QuestionMedia')
```

## Routes

### 1. **List Questions**
```
GET /level/<level_id>/questions
```
- Displays all questions for a level
- Shows statistics
- Provides quick actions

### 2. **Add Question**
```
GET/POST /level/<level_id>/questions/add
```
- GET: Shows add question form
- POST: Creates new question with media files

### 3. **Edit Question**
```
GET/POST /question/<question_id>/edit
```
- GET: Shows edit form with existing data
- POST: Updates question and media files

### 4. **Delete Question**
```
POST /question/<question_id>/delete
```
- Deletes question and all associated media files
- Removes files from filesystem

## User Interface

### Color Scheme
- **Text Type**: Info Blue (`#17a2b8`)
- **Image Type**: Success Green (`#28a745`)
- **Video Type**: Danger Red (`#dc3545`)
- **Mixed Type**: Warning Yellow (`#ffc107`)
- **Points**: Warning Yellow with star icon

### Icons
- Question: `bi-question-circle-fill`
- Add: `bi-plus-circle`
- Edit: `bi-pencil-square`
- Delete: `bi-trash`
- Media: `bi-paperclip`
- Clues: `bi-lightbulb`
- Points: `bi-star-fill`

### Responsive Design
- **Desktop**: Two-column layout for add/edit
- **Tablet**: Stacked columns
- **Mobile**: Full-width single column

## File Upload

### Naming Convention
```
{timestamp}_{original_filename}
```
Example: `1738694400_question_image.jpg`

### Storage
- Location: `/static/uploads/`
- Organized by upload time
- Automatic cleanup on deletion

### Security
- `secure_filename()` for sanitization
- File type validation
- Size limits (configurable)

## HTML Editor (TinyMCE)

### Configuration
```javascript
tinymce.init({
    selector: '#question_text',
    height: 400,
    plugins: [
        'advlist', 'autolink', 'lists', 'link', 'image',
        'charmap', 'preview', 'anchor', 'searchreplace',
        'visualblocks', 'code', 'fullscreen',
        'insertdatetime', 'media', 'table', 'help', 'wordcount'
    ],
    toolbar: 'undo redo | blocks | bold italic forecolor backcolor | 
              alignleft aligncenter alignright alignjustify | 
              bullist numlist outdent indent | removeformat | code | help'
});
```

### Features Available
- Undo/Redo
- Text blocks (headings, paragraphs)
- Bold, Italic, Colors
- Alignment
- Lists
- Indentation
- Code view
- Help documentation

## Migration

### Running the Migration
```bash
uv run python migrate_question_enhancements.py
```

### What It Does
1. Adds `points` column to questions table
2. Adds `updated_at` column to questions table
3. Creates `question_media` table
4. Migrates existing `media_url` to `question_media` table
5. Preserves backward compatibility

### Backward Compatibility
- Old `media_url` field retained
- Existing questions automatically migrated
- No data loss

## Usage Examples

### Example 1: Text Question with HTML
```html
<h3>What is the capital of France?</h3>
<p>Choose from the following options:</p>
<ul>
    <li>London</li>
    <li>Paris</li>
    <li>Berlin</li>
    <li>Madrid</li>
</ul>
```

### Example 2: Image Question
- Question Type: Image
- Question Text: "Identify the landmark in the image"
- Media Files:
  - Image 1: eiffel_tower.jpg (Caption: "Famous landmark")
- Answer: "Eiffel Tower"
- Points: 15

### Example 3: Mixed Media Question
- Question Type: Mixed
- Question Text: "Watch the video and answer the questions"
- Media Files:
  - Video 1: tutorial.mp4 (Caption: "Tutorial video")
  - Image 1: diagram.png (Caption: "Reference diagram")
  - Document 1: notes.pdf (Caption: "Additional notes")
- Answer: "Photosynthesis"
- Points: 20

## Statistics

### Question List Statistics
- **Total Questions**: Count of all questions
- **Total Media Files**: Sum of all media attachments
- **Total Clues**: Sum of all clues across questions
- **Total Points**: Sum of points for all questions

### Per-Question Display
- Question number badge
- Type badge with icon
- Text preview (truncated to 100 chars)
- Answer in code format
- Points with star icon
- Media count badge
- Clues count badge

## Best Practices

### Question Text
1. Use headings for structure
2. Format important text with bold/italic
3. Use lists for options
4. Keep it concise but clear
5. Add code blocks for technical questions

### Media Files
1. Add descriptive captions
2. Use appropriate file types
3. Optimize file sizes
4. Order media logically
5. Preview before saving

### Points Allocation
1. Easy questions: 5-10 points
2. Medium questions: 10-15 points
3. Hard questions: 15-25 points
4. Bonus questions: 25+ points

### Question Types
1. **Text Only**: For pure knowledge questions
2. **Image**: For visual identification
3. **Video**: For demonstrations
4. **Mixed**: For comprehensive challenges

## Validation

### Client-Side
- Required fields validation
- File type checking
- TinyMCE content validation
- Form submission prevention on errors

### Server-Side
- File upload validation
- Data sanitization
- Database constraints
- Error handling

## Error Handling

### Upload Errors
- File too large
- Invalid file type
- Upload failed
- Disk space issues

### Form Errors
- Missing required fields
- Invalid data types
- Duplicate question numbers
- Database errors

## Performance

### Optimizations
- Lazy loading of media
- Thumbnail generation (future)
- Pagination for large lists (future)
- Caching of statistics

### File Management
- Timestamp-based naming prevents conflicts
- Automatic cleanup on deletion
- Organized storage structure

## Security

### File Upload Security
- Filename sanitization
- Type validation
- Size limits
- Secure storage path

### XSS Prevention
- HTML sanitization in display
- TinyMCE built-in protection
- Template escaping

### Access Control
- Admin-only routes
- Authentication required
- Authorization checks

## Future Enhancements

### Planned Features
1. **Drag-and-Drop**: Reorder media files
2. **Bulk Upload**: Multiple files at once
3. **Media Library**: Reuse uploaded files
4. **Question Templates**: Pre-defined formats
5. **Import/Export**: JSON/CSV support
6. **Question Bank**: Reusable question pool
7. **Difficulty Levels**: Easy/Medium/Hard tags
8. **Categories**: Organize by topic
9. **Search**: Find questions quickly
10. **Preview**: See question as players will

### Technical Improvements
1. **Image Optimization**: Automatic resizing
2. **Video Transcoding**: Convert to web formats
3. **CDN Integration**: Faster media delivery
4. **Versioning**: Track question changes
5. **Analytics**: Question performance metrics

## Files Modified

### New Files
- `models.py` - Added QuestionMedia model
- `migrate_question_enhancements.py` - Migration script
- `templates/admin/manage_questions.html` - List view
- `templates/admin/add_edit_question.html` - Add/Edit form

### Modified Files
- `routes/admin.py` - Updated routes for new workflow
- `models.py` - Updated Question model

## Testing Checklist

- [x] Migration runs successfully
- [x] List view displays correctly
- [x] Add question form works
- [x] Edit question form works
- [x] HTML editor initializes
- [x] Media upload works
- [x] Multiple media files supported
- [x] Media captions saved
- [x] Media deletion works
- [x] Question deletion works
- [x] Statistics calculate correctly
- [x] Responsive design works
- [x] Form validation works
- [x] File type validation works

## Conclusion

The redesigned question management system provides a professional, feature-rich interface for creating engaging treasure hunt questions. The combination of HTML formatting, multiple media support, and an intuitive UI makes it easy to create complex, multimedia questions that enhance the player experience.

---

**Version**: 3.0.0  
**Date**: 2026-02-04  
**Status**: ✅ Complete and Tested
