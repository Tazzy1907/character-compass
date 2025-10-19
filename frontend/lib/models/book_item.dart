import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../icons/svgs.dart';

// Data model to represent the data from the API
class BookItem {
  final String name;
  final IconData icon;
  final String docId;
  final bool isProcessing;
  final String? error;
  final bool isActivelyMonitored;

  BookItem({
    required this.name,
    required this.icon,
    required this.docId,
    this.isProcessing = false,
    this.error,
    this.isActivelyMonitored = false,
  });

  // Factory constructor to create a CardItem from JSON.
  factory BookItem.fromJson(Map<String, dynamic> json) {
    try {
      return BookItem(
        name: json['name'] as String,
        icon: _mapStringToIcon(json['icon'] as String? ?? 'error'),
        docId: json['url'] as String,
        isProcessing: false, // Books from API are already processed
        error: null,
      );
    } catch (e) {
      // Re-throw the exception to let the caller handle it
      throw FormatException('Failed to parse BookItem: $e');
    }
  }

  // Copy method to update processing state
  BookItem copyWith({
    String? name,
    IconData? icon,
    String? docId,
    bool? isProcessing,
    String? error,
    bool? isActivelyMonitored,
  }) {
    return BookItem(
      name: name ?? this.name,
      icon: icon ?? this.icon,
      docId: docId ?? this.docId,
      isProcessing: isProcessing ?? this.isProcessing,
      error: error ?? this.error,
      isActivelyMonitored: isActivelyMonitored ?? this.isActivelyMonitored,
    );
  }
}

// Helper function to map an icon name (String) from the API to an IconData object.
IconData _mapStringToIcon(String iconName) {
  return iconMap[iconName] ?? FontAwesomeIcons.questionCircle;
}
