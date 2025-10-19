import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../assets/svgs.dart';

// Data model to represent the data from the API
class BookItem {
  final String name;
  final IconData icon;
  final String docId;

  BookItem({required this.name, required this.icon, required this.docId});

  // Factory constructor to create a CardItem from JSON.
  factory BookItem.fromJson(Map<String, dynamic> json) {
    try {
      return BookItem(
        name: json['name'] as String,
        icon: _mapStringToIcon(json['icon'] as String? ?? 'error'),
        docId: json['url'] as String,
      );
    } catch (e) {
      // Re-throw the exception to let the caller handle it
      throw FormatException('Failed to parse BookItem: $e');
    }
  }
}

// Helper function to map an icon name (String) from the API to an IconData object.
IconData _mapStringToIcon(String iconName) {
  return iconMap[iconName] ?? FontAwesomeIcons.questionCircle;
}
