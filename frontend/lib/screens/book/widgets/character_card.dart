import 'package:flutter/material.dart';
import 'package:frontend/style.dart';
import '../../../models/character_item.dart';
import '../../book/book_screen.dart';

// The card widget is now in its own file.
class CharacterCard extends StatelessWidget {
  final CharacterItem item;

  const CharacterCard({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      elevation: 4.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
      child: InkWell(
        onTap: () {
          print("Tapped on ${item.name}");
          Navigator.push(
            context,
            MaterialPageRoute(
              // Create an instance of DetailPage and
              // pass the value to its 'message' constructor parameter
              builder: (context) => BookScreen(bookId: ""),
            ),
          );
        },
        borderRadius: BorderRadius.circular(12.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              item.name,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 16.0,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16.0),
            Text(
              item.characterType,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 16.0,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
