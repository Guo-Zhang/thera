import 'package:flutter/material.dart';

import '../models/note.dart';
import 'note_detail_screen.dart';

class NotesListScreen extends StatelessWidget {
  final List<Note> notes;

  const NotesListScreen({super.key, required this.notes});

  @override
  Widget build(BuildContext context) {
    final folders = <String, List<Note>>{};
    for (final note in notes) {
      folders.putIfAbsent(note.folder, () => []).add(note);
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notes'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: ListView.builder(
        itemCount: notes.length,
        itemBuilder: (context, index) {
          final note = notes[index];
          return ListTile(
            title: Text(note.title),
            subtitle: Text(
              note.body.length > 50
                  ? '${note.body.substring(0, 50)}...'
                  : note.body,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            trailing: Chip(label: Text(note.folder)),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => NoteDetailScreen(note: note),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
