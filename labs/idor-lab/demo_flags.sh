#!/bin/bash

# Demo script to show FLAG generation with different emails

echo "🎯 IDOR Lab - FLAG Generation Demo"
echo "===================================="
echo ""
echo "This script demonstrates how FLAGS change based on EMAIL parameter"
echo ""

# Example 1
echo "📧 Example 1: EMAIL=long@mail.com"
echo "Input: 24112025_long@mail.com_IDOR"
echo -n "SHA1: "
echo -n "24112025_long@mail.com_IDOR" | sha1sum | awk '{print $1}'
echo ""

# Example 2
echo "📧 Example 2: EMAIL=admin@example.com"
echo "Input: 24112025_admin@example.com_IDOR"
echo -n "SHA1: "
echo -n "24112025_admin@example.com_IDOR" | sha1sum | awk '{print $1}'
echo ""

# Example 3
echo "📧 Example 3: EMAIL=student@university.edu"
echo "Input: 24112025_student@university.edu_IDOR"
echo -n "SHA1: "
echo -n "24112025_student@university.edu_IDOR" | sha1sum | awk '{print $1}'
echo ""

echo "===================================="
echo "💡 Tip: Use different emails to generate unique FLAGs!"
echo "      ENV=student_id EMAIL=your@email.com docker-compose up -d"
