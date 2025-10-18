import 'package:flutter/material.dart';

class AppTextField extends StatelessWidget {
  final TextEditingController controller;
  final String label;

  const AppTextField({
    super.key,
    required this.controller,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      cursorColor: Colors.white,
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.grey),
        floatingLabelStyle: TextStyle(
          color: Colors.white, // Custom color when focused
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Colors.grey, width: 2.5),
        ),
        // 2. Border when the TextField is focused
        focusedBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Colors.white, width: 2.5),
        ),
        // border: OutlineInputBorder(borderSide: BorderSide(width: 2)),
      ),
      style: const TextStyle(
        color: Colors.white, // The color of the text the user types
      ),
      autofocus: true,
    );
  }
}
