import 'dart:convert';

import 'package:flutter/services.dart';

import '../models/note.dart';

class NotesService {
  static Future<NotesExport> loadNotes() async {
    final contents = await rootBundle.loadString('assets/notes.json');
    final json = jsonDecode(contents) as Map<String, dynamic>;
    return NotesExport.fromJson(json);
  }
}
