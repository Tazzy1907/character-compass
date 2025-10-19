import 'package:flutter/material.dart';
import '../../../models/character_item.dart';
import './character_card.dart';

class ResponsiveCharacterGrid extends StatelessWidget {
  final List<CharacterItem> items;

  const ResponsiveCharacterGrid({super.key, required this.items});

  @override
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        const double desiredItemWidth = 150.0;
        final int crossAxisCount = (constraints.maxWidth / desiredItemWidth)
            .floor();

        return GridView.builder(
          padding: const EdgeInsets.all(16.0),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount > 0 ? crossAxisCount : 1,
            crossAxisSpacing: 16.0,
            mainAxisSpacing: 16.0,
            childAspectRatio: 1.0,
          ),
          itemCount: items.length,
          itemBuilder: (context, index) {
            return CharacterCard(item: items[index]);
          },
        );
      },
    );
  }
}
