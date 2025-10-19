import 'package:flutter/material.dart';
import '../../../models/book_item.dart';
import 'icon_card.dart';

class ResponsiveIconGrid extends StatelessWidget {
  final List<BookItem> items;
  final Function(String)? onCheckChanges;
  final Function(String)? onGenerate;

  const ResponsiveIconGrid({
    super.key,
    required this.items,
    this.onCheckChanges,
    this.onGenerate,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        const double desiredItemWidth =
            200.0; // Increased from 150 for bigger cards
        final int crossAxisCount = (constraints.maxWidth / desiredItemWidth)
            .floor();

        return GridView.builder(
          padding: const EdgeInsets.all(16.0),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount > 0 ? crossAxisCount : 1,
            crossAxisSpacing: 16.0,
            mainAxisSpacing: 16.0,
            childAspectRatio: 0.75, // Taller cards for bigger icons and buttons
          ),
          itemCount: items.length,
          itemBuilder: (context, index) {
            return IconCard(
              item: items[index],
              onCheckChanges: onCheckChanges,
              onGenerate: onGenerate,
            );
          },
        );
      },
    );
  }
}
