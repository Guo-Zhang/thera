class Note {
  final String title;
  final String body;
  final String folder;

  Note({required this.title, required this.body, required this.folder});

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      folder: json['folder'] as String? ?? '',
    );
  }
}

class NotesExport {
  final String exportDate;
  final int totalCount;
  final List<Note> notes;

  NotesExport({
    required this.exportDate,
    required this.totalCount,
    required this.notes,
  });

  factory NotesExport.fromJson(Map<String, dynamic> json) {
    return NotesExport(
      exportDate: json['export_date'] as String? ?? '',
      totalCount: json['total_count'] as int? ?? 0,
      notes:
          (json['notes'] as List<dynamic>?)
              ?.map((e) => Note.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}
