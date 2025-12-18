// Comparison utilities for face and text matching
const CompareUtil = (function() {
    // Face comparison simulation
    async function compareFacesSimulation(portraitImage, idImage) {
        // Simulate face detection and comparison
        return new Promise((resolve) => {
            setTimeout(() => {
                // Generate realistic match scores
                const baseScore = Math.random() * 0.3 + 0.7; // 70-100%
                const matchScore = Math.round(baseScore * 100);
                
                // Calculate feature matches
                const features = {
                    eyeDistance: Math.round((0.8 + Math.random() * 0.2) * 100),
                    noseShape: Math.round((0.75 + Math.random() * 0.25) * 100),
                    mouthPosition: Math.round((0.7 + Math.random() * 0.3) * 100),
                    faceShape: Math.round((0.65 + Math.random() * 0.35) * 100),
                    earPosition: Math.round((0.6 + Math.random() * 0.4) * 100)
                };
                
                // Determine overall facial landmarks match
                const landmarksMatch = Math.round(
                    Object.values(features).reduce((a, b) => a + b, 0) / Object.values(features).length
                );
                
                // Determine match status
                let matchStatus;
                if (matchScore >= 90) {
                    matchStatus = 'exact_match';
                } else if (matchScore >= 75) {
                    matchStatus = 'high_similarity';
                } else if (matchScore >= 60) {
                    matchStatus = 'moderate_similarity';
                } else {
                    matchStatus = 'low_similarity';
                }
                
                resolve({
                    success: true,
                    matchScore,
                    landmarksMatch,
                    matchStatus,
                    features,
                    confidence: Math.round((0.85 + Math.random() * 0.15) * 100),
                    details: {
                        faceDetected: true,
                        bothEyesVisible: Math.random() > 0.1,
                        frontalPose: Math.random() > 0.2,
                        goodLighting: Math.random() > 0.15,
                        noOcclusions: Math.random() > 0.25
                    }
                });
            }, 1500);
        });
    }

    // Text comparison
    function compareText(userText, extractedText, fieldType) {
        if (!userText || !extractedText) {
            return {
                match: false,
                score: 0,
                confidence: 0,
                details: 'Missing data for comparison'
            };
        }

        const normalizedUser = normalizeText(userText);
        const normalizedExtracted = normalizeText(extractedText);
        
        // Exact match
        if (normalizedUser === normalizedExtracted) {
            return {
                match: true,
                score: 100,
                confidence: 95,
                details: 'Exact match'
            };
        }

        // Calculate similarity score
        const similarity = calculateSimilarity(normalizedUser, normalizedExtracted);
        const score = Math.round(similarity * 100);
        
        // Determine match based on field type and threshold
        let matchThreshold = 90;
        let confidence = Math.round(similarity * 100);
        
        switch (fieldType) {
            case 'id_number':
                matchThreshold = 100; // ID numbers must match exactly
                confidence = similarity === 1 ? 95 : 50;
                break;
            case 'name':
                matchThreshold = 85;
                confidence = similarity > 0.9 ? 90 : 70;
                break;
            case 'date':
                matchThreshold = 100; // Dates must match exactly
                confidence = similarity === 1 ? 95 : 30;
                break;
            case 'nationality':
                matchThreshold = 90;
                confidence = similarity > 0.95 ? 92 : 60;
                break;
        }

        return {
            match: score >= matchThreshold,
            score,
            confidence,
            details: score >= matchThreshold ? 'Acceptable match' : 'Significant differences detected'
        };
    }

    // Normalize text for comparison
    function normalizeText(text) {
        return text.toString()
            .toLowerCase()
            .trim()
            .replace(/\s+/g, ' ') // Replace multiple spaces with single space
            .replace(/[^\w\s-]/g, '') // Remove special characters except hyphens
            .normalize('NFD').replace(/[\u0300-\u036f]/g, ''); // Remove diacritics
    }

    // Calculate text similarity using Levenshtein distance
    function calculateSimilarity(str1, str2) {
        if (str1 === str2) return 1;
        
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        // If one string is much longer than the other, similarity is low
        if (longer.length === 0 || shorter.length === 0) return 0;
        if (longer.length / shorter.length > 2) return 0;
        
        // Calculate Levenshtein distance
        const distance = levenshteinDistance(str1, str2);
        const maxLength = Math.max(str1.length, str2.length);
        
        return 1 - (distance / maxLength);
    }

    // Levenshtein distance algorithm
    function levenshteinDistance(str1, str2) {
        const matrix = [];
        
        // Initialize matrix
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        // Fill matrix
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1, // substitution
                        matrix[i][j - 1] + 1,     // insertion
                        matrix[i - 1][j] + 1      // deletion
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }

    // Compare ID information
    function compareIdInformation(userData, extractedData, idType) {
        const comparisonResults = {};
        let totalScore = 0;
        let fieldCount = 0;
        
        // Define fields to compare based on ID type
        const fieldsToCompare = getFieldsForIdType(idType);
        
        fieldsToCompare.forEach(field => {
            const userValue = userData[field.name];
            const extractedValue = extractedData[field.name];
            
            if (userValue !== undefined && extractedValue !== undefined) {
                const comparison = compareText(userValue, extractedValue, field.type);
                
                comparisonResults[field.name] = {
                    userValue,
                    extractedValue,
                    match: comparison.match,
                    score: comparison.score,
                    confidence: comparison.confidence,
                    details: comparison.details,
                    fieldLabel: field.label
                };
                
                totalScore += comparison.score;
                fieldCount++;
            }
        });
        
        // Calculate overall score
        const overallScore = fieldCount > 0 ? Math.round(totalScore / fieldCount) : 0;
        
        // Determine verification status
        let verificationStatus;
        let statusColor;
        
        if (overallScore >= 90) {
            verificationStatus = 'VALID';
            statusColor = 'green';
        } else if (overallScore >= 70) {
            verificationStatus = 'MISMATCH';
            statusColor = 'yellow';
        } else {
            verificationStatus = 'INVALID';
            statusColor = 'red';
        }
        
        return {
            overallScore,
            verificationStatus,
            statusColor,
            fieldCount,
            details: comparisonResults,
            summary: {
                matchedFields: Object.values(comparisonResults).filter(r => r.match).length,
                totalFields: fieldCount,
                averageConfidence: Math.round(
                    Object.values(comparisonResults).reduce((sum, r) => sum + r.confidence, 0) / fieldCount
                )
            }
        };
    }

    // Get fields to compare for each ID type
    function getFieldsForIdType(idType) {
        const fieldConfigs = {
            'ghana-card': [
                { name: 'cardNumber', label: 'Ghana Card Number', type: 'id_number' },
                { name: 'fullName', label: 'Full Name', type: 'name' },
                { name: 'dob', label: 'Date of Birth', type: 'date' },
                { name: 'expiryDate', label: 'Expiry Date', type: 'date' },
                { name: 'nationality', label: 'Nationality', type: 'nationality' }
            ],
            'passport': [
                { name: 'passportNumber', label: 'Passport Number', type: 'id_number' },
                { name: 'surname', label: 'Surname', type: 'name' },
                { name: 'otherNames', label: 'Other Names', type: 'name' },
                { name: 'dob', label: 'Date of Birth', type: 'date' },
                { name: 'nationality', label: 'Nationality', type: 'nationality' }
            ],
            'voter': [
                { name: 'voterId', label: 'Voter ID Number', type: 'id_number' },
                { name: 'name', label: 'Name', type: 'name' }
            ],
            'drivers': [
                { name: 'licenseNumber', label: 'License Number', type: 'id_number' },
                { name: 'licenseClass', label: 'License Class', type: 'name' },
                { name: 'dob', label: 'Date of Birth', type: 'date' }
            ]
        };
        
        return fieldConfigs[idType] || [];
    }

    // Generate comparison report
    function generateComparisonReport(faceComparison, textComparison) {
        const overallScore = Math.round(
            (faceComparison.matchScore + textComparison.overallScore) / 2
        );
        
        // Determine final verification result
        let finalResult;
        let resultColor;
        let resultMessage;
        
        if (overallScore >= 90 && faceComparison.matchScore >= 85 && textComparison.overallScore >= 85) {
            finalResult = 'VERIFICATION_SUCCESSFUL';
            resultColor = 'success';
            resultMessage = 'ID verification completed successfully. All checks passed.';
        } else if (overallScore >= 70) {
            finalResult = 'VERIFICATION_WITH_WARNINGS';
            resultColor = 'warning';
            resultMessage = 'ID verification completed with some discrepancies that require review.';
        } else {
            finalResult = 'VERIFICATION_FAILED';
            resultColor = 'error';
            resultMessage = 'ID verification failed. Significant discrepancies detected.';
        }
        
        return {
            finalResult,
            resultColor,
            resultMessage,
            overallScore,
            faceMatchScore: faceComparison.matchScore,
            textMatchScore: textComparison.overallScore,
            timestamp: new Date().toISOString(),
            details: {
                face: faceComparison,
                text: textComparison
            }
        };
    }

    // Format score for display
    function formatScore(score) {
        return {
            value: score,
            percentage: `${score}%`,
            color: score >= 90 ? 'text-green-600' : 
                   score >= 70 ? 'text-yellow-600' : 'text-red-600',
            bgColor: score >= 90 ? 'bg-green-100' : 
                    score >= 70 ? 'bg-yellow-100' : 'bg-red-100',
            label: score >= 90 ? 'Excellent' : 
                   score >= 70 ? 'Good' : 
                   score >= 50 ? 'Fair' : 'Poor'
        };
    }

    // Get match icon
    function getMatchIcon(matchStatus) {
        const icons = {
            exact_match: 'fas fa-check-circle text-green-500',
            high_similarity: 'fas fa-check-circle text-green-400',
            moderate_similarity: 'fas fa-exclamation-circle text-yellow-500',
            low_similarity: 'fas fa-times-circle text-red-500',
            no_match: 'fas fa-times-circle text-red-600'
        };
        
        return icons[matchStatus] || 'fas fa-question-circle text-gray-500';
    }

    return {
        compareFacesSimulation,
        compareText,
        compareIdInformation,
        generateComparisonReport,
        formatScore,
        getMatchIcon,
        normalizeText,
        calculateSimilarity
    };
})();

// Export for browser
if (typeof window !== 'undefined') {
    window.CompareUtil = CompareUtil;
}