import 'package:flutter/material.dart';

class BookScreen extends StatelessWidget {
  // 1. Declare the variable that will hold the passed value
  final String bookId;

  // 2. Require this value in the constructor
  const BookScreen({super.key, required this.bookId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Second Page')),
      body: Center(
        // 3. Use the value
        child: Text('The id is: $bookId', style: const TextStyle(fontSize: 24)),
      ),
    );
  }
}
