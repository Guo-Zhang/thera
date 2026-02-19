import 'dart:convert';
import 'dart:io';

import '../models/note.dart';

class NotesService {
  static Future<NotesExport> loadNotes() async {
    final file = File('../data/infra/apple/notes.json');
    final contents = await file.readAsString();
    final json = jsonDecode(contents) as Map<String, dynamic>;
    return NotesExport.fromJson(json);
  }
}
