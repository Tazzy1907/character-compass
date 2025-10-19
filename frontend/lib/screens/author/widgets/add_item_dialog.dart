import 'package:flutter/material.dart';
import '../../../models/book_item.dart';
import '../../../icons/svgs.dart';
import '../../../style.dart';
import '../../../api/api_service.dart';
import "app_text_field.dart";

class AddItemDialog extends StatefulWidget {
  const AddItemDialog({super.key});

  @override
  State<AddItemDialog> createState() => _AddItemDialogState();
}

class _AddItemDialogState extends State<AddItemDialog> {
  final _nameController = TextEditingController();
  final _urlController = TextEditingController();
  final _apiService = ApiService();

  IconData? _selectedIcon;
  bool _isLoading = false;

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

  void _submit() async {
    final name = _nameController.text;
    final url = _urlController.text;

    // Validate inputs
    if (name.isEmpty || url.isEmpty || _selectedIcon == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please fill in all fields and select an icon'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    final docId = extractGoogleDocId(url);
    if (docId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Invalid Google Docs URL'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Show loading state
    setState(() {
      _isLoading = true;
    });

    try {
      // Get icon name for API
      final iconName = _getIconName(_selectedIcon!);

      // Call API to upload book and trigger generation
      final result = await _apiService.uploadNewBook(docId, name, iconName);

      if (!mounted) return;

      if (result['success'] == true) {
        // Create book item with processing flag
        final newItem = BookItem(
          name: name,
          icon: _selectedIcon!,
          docId: docId,
          isProcessing: true,
        );

        // Pop the dialog and return the new item
        Navigator.of(context).pop(newItem);
      } else {
        // Show error message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Failed to upload book'),
            backgroundColor: Colors.red,
          ),
        );
        setState(() {
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
      setState(() {
        _isLoading = false;
      });
    }
  }

  String _getIconName(IconData icon) {
    // Find the icon name from the icon map
    for (var entry in publicIconMap.entries) {
      if (entry.value == icon) {
        return entry.key;
      }
    }
    return 'error';
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
            List<int> axisCounts = [8, 4, 2, 1];
            int crossAxisCount = 8;
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
            double iconSize = (crossAxisWidth * 0.5).clamp(24.0, 48.0);
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
                    child: Center(
                      child: GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
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
                                  color: isSelected
                                      ? Colors.white
                                      : Colors.grey,
                                  width: 2,
                                ),
                              ),
                              alignment: Alignment.center,
                              child: Icon(
                                icon,
                                size: iconSize,
                                color: Colors.white70,
                              ),
                            ),
                          );
                        },
                      ),
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
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Colors.white)),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
                  ),
                )
              : const Text('Add', style: TextStyle(color: Colors.black)),
        ),
      ],
    );
  }
}
