import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../assets/svgs.dart';

// Data model to represent the data from the API
class CardItem {
  final String name;
  final IconData icon;

  CardItem({required this.name, required this.icon});

  // Factory constructor to create a CardItem from JSON.
  factory CardItem.fromJson(Map<String, dynamic> json) {
    return CardItem(
      name: json['name'] as String? ?? 'Unnamed',
      icon: _mapStringToIcon(json['icon'] as String? ?? 'question'),
    );
  }
}

// Helper function to map an icon name (String) from the API to an IconData object.
IconData _mapStringToIcon(String iconName) {
  return iconMap[iconName] ?? FontAwesomeIcons.questionCircle;
}
