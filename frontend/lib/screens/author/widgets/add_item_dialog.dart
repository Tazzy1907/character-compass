import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../../../models/card_item.dart';
import '../../../icons/svgs.dart';
import '../../../style.dart';
import "app_text_field.dart";

class AddItemDialog extends StatefulWidget {
  const AddItemDialog({super.key});

  @override
  State<AddItemDialog> createState() => _AddItemDialogState();
}

class _AddItemDialogState extends State<AddItemDialog> {
  final _nameController = TextEditingController();
  final _urlController = TextEditingController();

  IconData? _selectedIcon;

  // A list of selectable icons for the user.
  final List<IconData> _selectableIcons = publicIconMap.values.toList();

  @override
  void dispose() {
    _nameController.dispose();
    _urlController.dispose();
    super.dispose();
  }

  String? extractGoogleDocId(String url) {
    // The document ID is a long string of characters and is typically
    // found after "/d/" and before the next "/".
    // This RegExp captures that group of characters.
    final regExp = RegExp(r'/document/d/([a-zA-Z0-9-_]+)');

    final match = regExp.firstMatch(url);

    // group(0) is the full match (e.g., "/document/d/12345/"),
    // group(1) is the first captured group (e.g., "12345").
    if (match != null && match.groupCount >= 1) {
      return match.group(1);
    }

    return null;
  }

  void _submit() {
    final name = _nameController.text;
    final url = _urlController.text;
    // Ensure a name has been entered and an icon has been selected
    if (name.isNotEmpty && url.isNotEmpty && _selectedIcon != null) {
      final docId = extractGoogleDocId(url);
      if (docId == null) return;
      final newItem = CardItem(name: name, icon: _selectedIcon!, docId: docId);
      // Pop the dialog and return the new item
      Navigator.of(context).pop(newItem);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: darkColor,
      title: const Text('Add New Book', style: TextStyle(color: Colors.white)),
      content: SingleChildScrollView(
        child: Builder(
          builder: (context) {
            double maxWidth = MediaQuery.of(context).size.width;
            int maxCrossAxisCount = (maxWidth / 65).floor();
            List<int> axisCounts = [16, 8, 4, 2, 1];
            int crossAxisCount = 16;
            for (int count in axisCounts) {
              if (maxCrossAxisCount >= count) {
                crossAxisCount = count;
                break;
              }
            }
            double crossAxisWidth =
                (maxWidth - (10 * 2) - (10 * (crossAxisCount - 1))) /
                crossAxisCount;
            int mainAxisCount = (_selectableIcons.length / crossAxisCount)
                .ceil();
            double height =
                20 +
                (10 * (mainAxisCount - 1)) +
                (mainAxisCount * crossAxisWidth);
            return Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppTextField(controller: _nameController, label: "Name"),
                const SizedBox(height: 20),
                AppTextField(
                  controller: _urlController,
                  label: "Google Docs Link",
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: maxWidth,
                  height: height,
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'Icon',
                      floatingLabelStyle: TextStyle(
                        color: Colors.grey,
                        fontSize: 20, // Custom color when focused
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey, width: 2.5),
                        borderRadius: BorderRadius.all(Radius.circular(12)),
                      ),
                      // You might want to adjust padding
                      // to make it look just right.
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16.0,
                        vertical: 16.0,
                      ),
                    ),
                    // We set isEmpty to false to force the label to "float"
                    // Otherwise, it might sit on top of your icons.
                    isEmpty: false,
                    child: GridView.builder(
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: crossAxisCount,
                        crossAxisSpacing: 10,
                        mainAxisSpacing: 10,
                      ),
                      itemCount: _selectableIcons.length,
                      itemBuilder: (context, index) {
                        final icon = _selectableIcons[index];
                        final isSelected = _selectedIcon == icon;
                        return GestureDetector(
                          onTap: () {
                            setState(() {
                              _selectedIcon = icon;
                            });
                          },
                          child: Container(
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? Theme.of(
                                      context,
                                    ).primaryColor.withOpacity(0.3)
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: isSelected ? Colors.white : Colors.grey,
                                width: 2,
                              ),
                            ),
                            child: Icon(icon, color: Colors.white70),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Colors.white)),
        ),
        ElevatedButton(
          onPressed: _submit,
          child: const Text('Add', style: TextStyle(color: Colors.black)),
        ),
      ],
    );
  }
}
