import 'package:flutter_test/flutter_test.dart';

import 'package:studio/main.dart';

void main() {
  testWidgets('App loads', (WidgetTester tester) async {
    await tester.pumpWidget(const StudioApp());
    expect(find.text('Studio'), findsOneWidget);
  });
}
