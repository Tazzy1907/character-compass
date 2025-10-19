import 'package:flutter/material.dart';
import '../author/author_screen.dart';
import '../../../style.dart';

// 1. The Landing Page Widget
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Set the background color for the entire screen
      backgroundColor: darkColor, // A dark slate blue color
      // Use a GestureDetector to make the entire body clickable
      body: GestureDetector(
        // The action to perform on tap
        onTap: () {
          // Use pushReplacement to go to the home page so the user
          // can't press the back button to return to the landing page.
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (context) => const AuthorScreen()),
          );
        },
        behavior: HitTestBehavior.opaque,
        child: Center(
          // Center the image on the screen
          child: Image.asset(
            'icons/Character Compass No BG.png', // The path to your image asset
            width: 300, // Optional: control the size of your image
            height: 300,
          ),
        ),
      ),
    );
  }
}
