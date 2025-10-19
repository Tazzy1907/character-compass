import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:frontend/style.dart';
import '../../../models/book_item.dart';
import '../../book/book_screen.dart';

// The card widget is now in its own file.
class IconCard extends StatelessWidget {
  final BookItem item;
  final Function(String)? onToggleMonitoring;

  const IconCard({super.key, required this.item, this.onToggleMonitoring});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      elevation: 4.0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12.0),
        side: item.isActivelyMonitored
            ? const BorderSide(color: Colors.green, width: 3.0)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: item.isProcessing
            ? null
            : () {
                print("Tapped on ${item.name}");
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => BookScreen(bookId: item.docId),
                  ),
                );
              },
        borderRadius: BorderRadius.circular(12.0),
        child: Stack(
          children: [
            // Main content
            SizedBox.expand(
              child: Opacity(
                opacity: item.isProcessing ? 0.5 : 1.0,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    FaIcon(item.icon, size: 48.0, color: lightColor),
                    const SizedBox(height: 16.0),
                    Text(
                      item.name,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 16.0,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // Processing overlay
            if (item.isProcessing)
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(12.0),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                      const SizedBox(height: 8.0),
                      const Text(
                        'Processing...',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12.0,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            // Error indicator
            if (item.error != null && !item.isProcessing)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.red,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.error, color: Colors.white, size: 20),
                ),
              ),
            // Monitoring toggle button
            if (!item.isProcessing && onToggleMonitoring != null)
              Positioned(
                bottom: 8,
                right: 8,
                child: GestureDetector(
                  onTap: () {
                    onToggleMonitoring!(item.docId);
                  },
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: item.isActivelyMonitored
                          ? Colors.green
                          : Colors.grey[700],
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.2),
                          blurRadius: 4,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Icon(
                      item.isActivelyMonitored
                          ? Icons.visibility
                          : Icons.visibility_off,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
